"""
Application configuration: model catalog and related constants.
"""

AVAILABLE_MODELS = [
    {
        "id": "openai/gpt-4o-mini",
        "label": "GPT-4o Mini (OpenAI)",
    },
    {
        "id": "anthropic/claude-3-5-haiku",
        "label": "Claude 3.5 Haiku (Anthropic)",
    },
    {
        "id": "google/gemini-2.0-flash-001",
        "label": "Gemini 2.0 Flash (Google)",
    },
    {
        "id": "openai/gpt-4o",
        "label": "GPT-4o (OpenAI)",
    },
    {
        "id": "anthropic/claude-3-5-sonnet",
        "label": "Claude 3.5 Sonnet (Anthropic)",
    },
    {
        "id": "google/gemini-2.5-pro-preview",
        "label": "Gemini 2.5 Pro (Google)",
    },
    {
        "id": "meta-llama/llama-3.1-70b-instruct",
        "label": "Llama 3.1 70B (Meta)",
    },
    {
        "id": "mistralai/mistral-large",
        "label": "Mistral Large (Mistral)",
    },
]

DEFAULT_MODELS = [
    "openai/gpt-4o-mini",
    "anthropic/claude-3-5-haiku",
    "google/gemini-2.0-flash-001",
]

JUDGE_MODEL = "openai/gpt-4o"

JUDGE_SYSTEM_PROMPT = """
You are an impartial AI response evaluator.
You will receive a user prompt and multiple AI model responses with \
their response times.

Evaluate each response on these criteria (score 1-10):
- accuracy: factual correctness and direct relevance to the question
- conciseness: how focused and non-repetitive the response is
- tone: appropriateness of tone for the context
- speed: relative response time compared to other models \
(faster = higher score)

Return ONLY valid JSON in this exact schema. No other text, no markdown fences:
{
  "evaluations": [
    {
      "model": "<model_id exactly as provided>",
      "scores": {
        "accuracy": <integer 1-10>,
        "conciseness": <integer 1-10>,
        "tone": <integer 1-10>,
        "speed": <integer 1-10>
      },
      "reasoning": "<one sentence summary of your assessment>"
    }
  ],
  "winner": "<model_id of the best overall response>"
}
"""
