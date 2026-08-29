"""
Shared helper for loading and validating LLM provider API keys from a .env file.

Usage (from any notebook/script in this project):

    from util import check_api_key, load_keys

    # Check a single provider - prints a friendly message and returns the key (or None)
    openai_api_key = check_api_key("openai")

    # Check every known provider at once, returns a dict of {provider: key_or_None}
    keys = load_keys()
"""

import os
from dotenv import load_dotenv

# Maps a provider name -> the env var name it's stored under in .env
# Add new providers here and every helper below picks them up automatically.
PROVIDER_ENV_VARS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "groq": "GROQ_API_KEY",
    "grok": "GROK_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}

# How many leading characters of the key are safe to print for debugging
_PREVIEW_LEN = 8

_dotenv_loaded = False


def _ensure_dotenv_loaded(override: bool = True):
    """Load .env once per process (idempotent, but honors override on first call)."""
    global _dotenv_loaded
    if not _dotenv_loaded:
        load_dotenv(override=override)
        _dotenv_loaded = True


def check_api_key(provider: str, verbose: bool = True) -> str | None:
    """
    Fetch the API key for `provider` from the environment (loading .env if needed)
    and print a message saying whether it exists.

    provider: one of the keys in PROVIDER_ENV_VARS (case-insensitive), e.g. "openai".
    verbose: set False to suppress the printed message.

    Returns the key string if set, otherwise None.
    """
    _ensure_dotenv_loaded()

    provider_key = provider.lower()
    if provider_key not in PROVIDER_ENV_VARS:
        known = ", ".join(sorted(PROVIDER_ENV_VARS))
        raise ValueError(f"Unknown provider '{provider}'. Known providers: {known}")

    env_var = PROVIDER_ENV_VARS[provider_key]
    api_key = os.getenv(env_var)
    label = provider_key.capitalize()

    if verbose:
        if api_key:
            print(f"{label} API Key exists and begins {api_key[:_PREVIEW_LEN]}")
        else:
            print(f"{label} API Key not set")

    return api_key


def load_keys(providers: list[str] | None = None, verbose: bool = True) -> dict:
    """
    Check a list of providers (defaults to all known providers) in one call.

    Returns a dict of {provider: key_or_None}.
    """
    providers = providers or list(PROVIDER_ENV_VARS)
    return {provider: check_api_key(provider, verbose=verbose) for provider in providers}


if __name__ == "__main__":
    # Quick manual check: `python util.py`
    load_keys()
