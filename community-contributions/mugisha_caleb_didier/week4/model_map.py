# Mapping of unprefixed model names found in the course to their exact OpenRouter IDs.
# Used by the converter's SYSTEM_PROMPT so the LLM gets deterministic model name mappings
# instead of relying on vague wildcard prefix rules.

MODEL_MAP = {
    # OpenAI
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o-mini": "openai/gpt-4o-mini",
    "gpt-4.1": "openai/gpt-4.1",
    "gpt-4.1-mini": "openai/gpt-4.1-mini",
    "gpt-4.1-nano": "openai/gpt-4.1-nano",
    "gpt-5": "openai/gpt-5",
    "gpt-5-mini": "openai/gpt-5-mini",
    "gpt-5-nano": "openai/gpt-5-nano",
    "gpt-5.1": "openai/gpt-5.1",
    "gpt-5.2": "openai/gpt-5.2",
    # Anthropic
    "claude-sonnet-4-5-20250929": "anthropic/claude-sonnet-4-5-20250929",
    "claude-sonnet-4.5": "anthropic/claude-sonnet-4.5",
    "claude-sonnet-4.6": "anthropic/claude-sonnet-4.6",
    "claude-opus-4.5": "anthropic/claude-opus-4.5",
    "claude-opus-4.6": "anthropic/claude-opus-4.6",
    "claude-haiku-4-5": "anthropic/claude-haiku-4-5",
    "claude-3.5-haiku": "anthropic/claude-3.5-haiku",
    # Google
    "gemini-2.0-flash": "google/gemini-2.0-flash",
    "gemini-2.5-flash-lite": "google/gemini-2.5-flash-lite",
    "gemini-2.5-pro": "google/gemini-2.5-pro",
    "gemini-3-flash-preview": "google/gemini-3-flash-preview",
    "gemini-3-pro-preview": "google/gemini-3-pro-preview",
    # xAI
    "grok-2": "x-ai/grok-2",
    "grok-4": "x-ai/grok-4",
    # DeepSeek
    "deepseek-coder-v2": "deepseek/deepseek-coder-v2",
    "deepseek-chat": "deepseek/deepseek-chat",
}
