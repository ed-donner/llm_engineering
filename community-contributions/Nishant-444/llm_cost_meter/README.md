# LLM Cost Meter

Tracks token usage and estimated API spend across the providers used on this course.

The course keeps total costs to a few dollars, but never shows what an individual
call costs. This adds that, in about 300 lines and with no new dependencies.

Because the course drives OpenAI, Anthropic, Gemini, DeepSeek, Groq, Grok,
OpenRouter and Ollama through the same OpenAI client with a different `base_url`,
wrapping one method instruments all of them.

## Use

```python
from openai import OpenAI
from cost_meter import CostMeter

meter = CostMeter()
openai = meter.wrap(OpenAI())

response = openai.chat.completions.create(model="gpt-5-nano", messages=messages)

meter.report()
```

`wrap` patches the client in place and returns it, so existing code needs no
other change.

```
model                        calls        in       out  reason  cached        USD
---------------------------------------------------------------------------------
gpt-5-nano                       2     2,000       550     128       0   0.000320
claude-sonnet-4-5-20250929       1     2,000       900       0       0   0.019500
llama3.2                         1       500       300       0       0   0.000000
```

`meter.rows()` yields per-call dicts for pandas. `meter.total_cost` and
`meter.total_tokens` give running totals. `meter.label = "..."` tags subsequent
calls, which is useful when comparing settings.

## Why the reasoning column

`week2/day1.ipynb` varies `reasoning_effort` on the puzzle prompts. Reasoning
tokens are billed as output but never appear in the reply, so raising the effort
costs more with nothing visible to show for it. The meter breaks them out.

## Accuracy

Token counts are reported by the provider and are exact.

Costs are estimates from the table in `cost_meter.py`, dated by `PRICES_AS_OF`.
Check them against current pricing pages, and override with
`CostMeter(prices={...})` rather than editing the file.

Cached-input and batch discounts are not modelled, so a run that benefits from
prompt caching costs less than reported, never more. Models served from
localhost count as free. A model absent from the table is reported as `unpriced`
rather than silently counted as zero.

## Files

- `cost_meter.py` - the module
- `demo.ipynb` - worked examples, including the reasoning-effort comparison
