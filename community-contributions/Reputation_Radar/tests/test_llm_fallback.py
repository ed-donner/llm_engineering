import pytest

from services import llm
from services.utils import ServiceWarning


def test_llm_fallback_uses_vader():
    service = llm.LLMService(api_key=None)
    results = service.classify_sentiment_batch(
        ["I absolutely love this product!", "This is the worst experience ever."]
    )
    assert results[0].label == "positive"
    assert results[1].label == "negative"


def test_summary_requires_openai_key():
    service = llm.LLMService(api_key=None)
    with pytest.raises(ServiceWarning):
        service.summarize_overall([{"label": "positive", "text": "Example"}])
