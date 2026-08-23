"""Zero-shot and fine-tuned price predictors for Week 6 comparison and Gradio UI."""
import os
import re
from openai import OpenAI
from litellm import completion

# Same prompt format as week6 day4/day5
def messages_for_item(item_or_text):
    """Build user message for pricing. Accepts an Item (with .summary) or a raw description string."""
    text = item_or_text.summary if hasattr(item_or_text, "summary") and item_or_text.summary else str(item_or_text)
    return [{"role": "user", "content": f"Estimate the price of this product. Respond with the price, no explanation\n\n{text}"}]


def post_process(value):
    """Extract numeric price from model output (matches pricer.evaluator.Tester.post_process)."""
    if isinstance(value, str):
        value = value.replace("$", "").replace(",", "")
        match = re.search(r"[-+]?\d*\.\d+|\d+", value)
        return float(match.group()) if match else 0.0
    return float(value)


# Zero-shot: LiteLLM (e.g. gpt-4.1-nano)
ZERO_SHOT_MODEL = os.environ.get("WEEK6_ZERO_SHOT_MODEL", "openai/gpt-4.1-nano")


def zero_shot_predict(item_or_text, model=ZERO_SHOT_MODEL):
    """Predict price using zero-shot LLM."""
    response = completion(model=model, messages=messages_for_item(item_or_text))
    return post_process(response.choices[0].message.content)


# Fine-tuned: OpenAI API (your fine-tuned model name)
FINE_TUNED_MODEL = os.environ.get("WEEK6_FINE_TUNED_MODEL", "")


def fine_tuned_predict(item_or_text, model=None):
    """Predict price using fine-tuned model. Set WEEK6_FINE_TUNED_MODEL or pass model."""
    name = model or FINE_TUNED_MODEL
    if not name:
        raise ValueError("Set WEEK6_FINE_TUNED_MODEL or pass model= to fine_tuned_predict")
    client = OpenAI()
    response = client.chat.completions.create(
        model=name,
        messages=messages_for_item(item_or_text),
        max_tokens=7,
    )
    return post_process(response.choices[0].message.content)
