"""Token and spend metering for the providers used on this course.

The course drives OpenAI, Anthropic, Gemini, DeepSeek, Groq, Grok, OpenRouter and
Ollama through the same OpenAI client with a different base_url, so wrapping a
single method instruments all of them:

    from openai import OpenAI
    from cost_meter import CostMeter

    meter = CostMeter()
    openai = meter.wrap(OpenAI())

    response = openai.chat.completions.create(model="gpt-5-nano", messages=messages)

    meter.report()

Existing course code needs no other changes: wrap() patches the client in place
and returns it, so every later chat.completions.create call is recorded.

Two things worth knowing about the numbers:

* Token counts are reported by the provider, so they are exact.
* Costs are estimates from the table below. Cached-input discounts and batch
  discounts are deliberately not modelled, so a run that benefits from prompt
  caching will cost less than reported, never more.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

# List prices in USD per million tokens, as (input, output).
# Verify against the provider's pricing page before trusting these for anything
# that matters; override with CostMeter(prices={...}) rather than editing here.
PRICES_AS_OF = "2026-01"

PRICES: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-5": (1.25, 10.00),
    "gpt-5-mini": (0.25, 2.00),
    "gpt-5-nano": (0.05, 0.40),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    # Anthropic
    "claude-opus-4-1": (15.00, 75.00),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-3-haiku": (0.25, 1.25),
    # Google
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
    # DeepSeek
    "deepseek-chat": (0.27, 1.10),
    "deepseek-reasoner": (0.55, 2.19),
    # Groq
    "gpt-oss-120b": (0.15, 0.75),
    "gpt-oss-20b": (0.10, 0.50),
    # xAI
    "grok-4": (3.00, 15.00),
}

# Anything served from these hosts runs locally and is free.
LOCAL_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0")

PROVIDER_BY_HOST = {
    "api.openai.com": "openai",
    "api.anthropic.com": "anthropic",
    "generativelanguage.googleapis.com": "google",
    "api.deepseek.com": "deepseek",
    "api.groq.com": "groq",
    "api.x.ai": "xai",
    "openrouter.ai": "openrouter",
}

_DATE_SUFFIX = re.compile(r"-\d{8}$")


def normalise(model: str) -> str:
    """Reduce a model id to the key used in PRICES.

    Handles the three shapes the course produces: plain ids (gpt-5-nano),
    namespaced ids from Groq and OpenRouter (openai/gpt-oss-120b), and Ollama
    tags (gpt-oss:20b). Anthropic's dated ids lose the trailing date.
    """
    name = model.strip().lower()
    if "/" in name:
        name = name.rsplit("/", 1)[-1]
    if ":" in name:
        name = name.split(":", 1)[0]
    return _DATE_SUFFIX.sub("", name)


def look_up_price(model: str, prices: dict[str, tuple[float, float]]) -> tuple[float, float] | None:
    """Find rates for a model, or None if it is not in the table."""
    name = normalise(model)
    if name in prices:
        return prices[name]
    # Fall back to the longest key that prefixes the name, so a dated or
    # suffixed variant still matches its family.
    candidates = [key for key in prices if name.startswith(key)]
    if candidates:
        return prices[max(candidates, key=len)]
    return None


@dataclass
class Call:
    """One recorded chat.completions.create call."""

    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int = 0
    cached_tokens: int = 0
    cost: float | None = None
    label: str = ""

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def priced(self) -> bool:
        return self.cost is not None


@dataclass
class CostMeter:
    """Records token usage and estimated spend across wrapped clients."""

    prices: dict[str, tuple[float, float]] = field(default_factory=lambda: dict(PRICES))
    calls: list[Call] = field(default_factory=list)
    label: str = ""
    _patched: list[Any] = field(default_factory=list, repr=False)

    # -- wiring ---------------------------------------------------------

    def wrap(self, client: Any, provider: str | None = None) -> Any:
        """Patch a client's chat.completions.create to record usage.

        Returns the same client, so it can be used inline. Wrapping a client
        twice is a no-op.
        """
        completions = client.chat.completions
        if getattr(completions, "_cost_meter", None) is not None:
            return client

        if provider is None:
            provider = self.detect_provider(client)
        # Remember whether create was already an instance attribute, so unwrap
        # can restore the class method rather than leaving a shadow behind.
        had_own_create = "create" in vars(completions)
        original = completions.create

        def create(*args: Any, **kwargs: Any) -> Any:
            response = original(*args, **kwargs)
            self.record(
                model=kwargs.get("model") or getattr(response, "model", "unknown"),
                usage=getattr(response, "usage", None),
                provider=provider,
            )
            return response

        completions.create = create
        completions._cost_meter = self
        self._patched.append((completions, original, had_own_create))
        return client

    def unwrap_all(self) -> None:
        """Restore every patched client. Recorded calls are kept."""
        for completions, original, had_own_create in self._patched:
            if had_own_create:
                completions.create = original
            else:
                del completions.create
            completions._cost_meter = None
        self._patched.clear()

    @staticmethod
    def detect_provider(client: Any) -> str:
        """Infer the provider from the client's base_url."""
        host = ""
        base_url = getattr(client, "base_url", None)
        if base_url is not None:
            host = (getattr(base_url, "host", None) or str(base_url)).lower()
        if any(local in host for local in LOCAL_HOSTS):
            return "ollama"
        for known, name in PROVIDER_BY_HOST.items():
            if known in host:
                return name
        return "unknown"

    # -- recording ------------------------------------------------------

    def record(self, model: str, usage: Any, provider: str = "unknown") -> Call | None:
        """Record one call. Returns None if the response carried no usage."""
        if usage is None:
            return None

        completion_details = getattr(usage, "completion_tokens_details", None)
        prompt_details = getattr(usage, "prompt_tokens_details", None)

        call = Call(
            model=model,
            provider=provider,
            # prompt_tokens already includes cached tokens, and completion_tokens
            # already includes reasoning tokens. Both are broken out for insight
            # only, and must not be added to the totals again.
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
            reasoning_tokens=getattr(completion_details, "reasoning_tokens", 0) or 0,
            cached_tokens=getattr(prompt_details, "cached_tokens", 0) or 0,
            label=self.label,
        )
        call.cost = self.estimate(call)
        self.calls.append(call)
        return call

    def estimate(self, call: Call) -> float | None:
        """Cost in USD, 0.0 for local models, or None if the model is unpriced."""
        if call.provider == "ollama":
            return 0.0
        rates = look_up_price(call.model, self.prices)
        if rates is None:
            return None
        input_rate, output_rate = rates
        return (call.input_tokens * input_rate + call.output_tokens * output_rate) / 1_000_000

    def reset(self) -> None:
        self.calls.clear()

    # -- reading --------------------------------------------------------

    @property
    def total_cost(self) -> float:
        """Estimated spend, counting unpriced calls as zero."""
        return sum(call.cost or 0.0 for call in self.calls)

    @property
    def total_tokens(self) -> int:
        return sum(call.total_tokens for call in self.calls)

    @property
    def unpriced(self) -> list[Call]:
        return [call for call in self.calls if not call.priced]

    def by_model(self) -> dict[str, dict[str, Any]]:
        """Aggregate calls per model, in first-seen order."""
        grouped: dict[str, dict[str, Any]] = {}
        for call in self.calls:
            row = grouped.setdefault(
                call.model,
                {
                    "provider": call.provider,
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "reasoning_tokens": 0,
                    "cached_tokens": 0,
                    "cost": 0.0,
                    "priced": True,
                },
            )
            row["calls"] += 1
            row["input_tokens"] += call.input_tokens
            row["output_tokens"] += call.output_tokens
            row["reasoning_tokens"] += call.reasoning_tokens
            row["cached_tokens"] += call.cached_tokens
            row["cost"] += call.cost or 0.0
            row["priced"] = row["priced"] and call.priced
        return grouped

    def report(self, show: bool = True) -> str:
        """Build a plain-text summary, printing it unless show is False."""
        if not self.calls:
            text = "No calls recorded yet."
            if show:
                print(text)
            return text

        header = f"{'model':<28}{'calls':>6}{'in':>10}{'out':>10}{'reason':>8}{'cached':>8}{'USD':>11}"
        lines = [header, "-" * len(header)]

        for model, row in self.by_model().items():
            cost = f"{row['cost']:.6f}" if row["priced"] else "unpriced"
            lines.append(
                f"{model[:28]:<28}{row['calls']:>6}{row['input_tokens']:>10,}"
                f"{row['output_tokens']:>10,}{row['reasoning_tokens']:>8,}"
                f"{row['cached_tokens']:>8,}{cost:>11}"
            )

        lines.append("-" * len(header))
        lines.append(
            f"{'total':<28}{len(self.calls):>6}"
            f"{sum(c.input_tokens for c in self.calls):>10,}"
            f"{sum(c.output_tokens for c in self.calls):>10,}"
            f"{sum(c.reasoning_tokens for c in self.calls):>8,}"
            f"{sum(c.cached_tokens for c in self.calls):>8,}"
            f"{self.total_cost:>11.6f}"
        )
        lines.append("")
        lines.append(f"Estimated spend: ${self.total_cost:.4f} (list prices as of {PRICES_AS_OF})")

        missing = sorted({call.model for call in self.unpriced})
        if missing:
            lines.append(
                "Not counted, no price on file: " + ", ".join(missing)
                + ". Pass prices={...} to CostMeter to include them."
            )

        text = "\n".join(lines)
        if show:
            print(text)
        return text

    def rows(self) -> Iterable[dict[str, Any]]:
        """Per-call dicts, ready for pandas.DataFrame if you want to chart them."""
        for call in self.calls:
            yield {
                "model": call.model,
                "provider": call.provider,
                "label": call.label,
                "input_tokens": call.input_tokens,
                "output_tokens": call.output_tokens,
                "reasoning_tokens": call.reasoning_tokens,
                "cached_tokens": call.cached_tokens,
                "cost": call.cost,
            }
