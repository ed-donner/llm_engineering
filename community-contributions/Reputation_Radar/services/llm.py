"""LLM sentiment analysis and summarization utilities."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

try:  # pragma: no cover - optional dependency
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .utils import ServiceWarning, chunked

CLASSIFICATION_SYSTEM_PROMPT = "You are a precise brand-sentiment classifier. Output JSON only."
SUMMARY_SYSTEM_PROMPT = "You analyze brand chatter and produce concise, executive-ready summaries."


@dataclass
class SentimentResult:
    """Structured sentiment output."""

    label: str
    confidence: float


class LLMService:
    """Wrapper around OpenAI with VADER fallback."""

    def __init__(self, api_key: Optional[str], model: str = "gpt-4o-mini", batch_size: int = 20):
        self.batch_size = max(1, batch_size)
        self.model = model
        self.logger = logging.getLogger("services.llm")
        self._client: Optional[Any] = None
        self._analyzer = SentimentIntensityAnalyzer()
        if api_key and OpenAI is not None:
            try:
                self._client = OpenAI(api_key=api_key)
            except Exception as exc:  # noqa: BLE001
                self.logger.warning("Failed to initialize OpenAI client, using VADER fallback: %s", exc)
                self._client = None
        elif api_key and OpenAI is None:
            self.logger.warning("openai package not installed; falling back to VADER despite API key.")

    def available(self) -> bool:
        """Return whether OpenAI-backed features are available."""
        return self._client is not None

    def classify_sentiment_batch(self, texts: Sequence[str]) -> List[SentimentResult]:
        """Classify multiple texts, chunking if necessary."""
        if not texts:
            return []
        if not self.available():
            return [self._vader_sentiment(text) for text in texts]

        results: List[SentimentResult] = []
        for chunk in chunked(list(texts), self.batch_size):
            prompt_lines = ["Classify each item as \"positive\", \"neutral\", or \"negative\".", "Also output a confidence score between 0 and 1.", "Return an array of objects: [{\"label\": \"...\", \"confidence\": 0.0}].", "Items:"]
            prompt_lines.extend([f"{idx + 1}) {text}" for idx, text in enumerate(chunk)])
            prompt = "\n".join(prompt_lines)
            try:
                response = self._client.responses.create(  # type: ignore[union-attr]
                    model=self.model,
                    input=[
                        {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0,
                    max_output_tokens=500,
                )
                output_text = self._extract_text(response)
                parsed = json.loads(output_text)
                for item in parsed:
                    results.append(
                        SentimentResult(
                            label=item.get("label", "neutral"),
                            confidence=float(item.get("confidence", 0.5)),
                        )
                    )
            except Exception as exc:  # noqa: BLE001
                self.logger.warning("Classification fallback to VADER due to error: %s", exc)
                for text in chunk:
                    results.append(self._vader_sentiment(text))
        # Ensure the output length matches input
        if len(results) != len(texts):
            # align by padding with neutral
            results.extend([SentimentResult(label="neutral", confidence=0.33)] * (len(texts) - len(results)))
        return results

    def summarize_overall(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create an executive summary using OpenAI."""
        if not self.available():
            raise ServiceWarning("OpenAI API key missing. Summary unavailable.")
        prompt_lines = [
            "Given these labeled items and their short rationales, write:",
            "- 5 bullet \"Highlights\"",
            "- 5 bullet \"Risks & Concerns\"",
            "- One-line \"Overall Tone\" (Positive/Neutral/Negative with brief justification)",
            "- 3 \"Recommended Actions\"",
            "Keep it under 180 words total. Be specific but neutral in tone.",
            "Items:",
        ]
        for idx, item in enumerate(findings, start=1):
            prompt_lines.append(
                f"{idx}) [{item.get('label','neutral').upper()}] {item.get('text','')}"
            )
        prompt = "\n".join(prompt_lines)
        try:
            response = self._client.responses.create(  # type: ignore[union-attr]
                model=self.model,
                input=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_output_tokens=800,
            )
            output_text = self._extract_text(response)
            return {"raw": output_text}
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to generate summary: %s", exc)
            raise ServiceWarning("Unable to generate executive summary at this time.") from exc

    def _vader_sentiment(self, text: str) -> SentimentResult:
        scores = self._analyzer.polarity_scores(text)
        compound = scores["compound"]
        if compound >= 0.2:
            label = "positive"
        elif compound <= -0.2:
            label = "negative"
        else:
            label = "neutral"
        confidence = min(1.0, max(0.0, abs(compound)))
        return SentimentResult(label=label, confidence=confidence)

    def _extract_text(self, response: Any) -> str:
        """Support multiple OpenAI client response shapes."""
        if hasattr(response, "output") and response.output:
            content = response.output[0].content[0]
            return getattr(content, "text", str(content))
        if hasattr(response, "choices"):
            return response.choices[0].message.content  # type: ignore[return-value]
        raise ValueError("Unknown response structure from OpenAI client.")
