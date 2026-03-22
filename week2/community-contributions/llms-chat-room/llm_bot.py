import os

from dotenv import load_dotenv
from openai import OpenAI
import anthropic

LLM_BOT_CONFIGS = {
    "gpt": {
        "id": "gpt",
        "name": "Giorgio",
        "model": "gpt-4.1-nano",
        "api_key_env": "OPENAI_API_KEY",
    },
    "claude": {
        "id": "claude",
        "name": "Anna",
        "model": "claude-sonnet-4-20250514",
        "api_key_env": "ANTHROPIC_API_KEY",
    },
    "gemini": {
        "id": "gemini",
        "name": "Isabella",
        "model": "gemini-2.0-flash",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GOOGLE_API_KEY",
    },
    "openai": {
        "id": "openai",
        "name": "Marco",
        "model": "gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY",
    },
    "deepseek": {
        "id": "deepseek",
        "name": "Roberto",
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY"
    }
}


def load_api_key():
    """Load .env and ensure all required API keys from LLM_BOT_CONFIGS are present.

    - Reads environment variables from .env without overriding already-set envs.
    - Collects unique api_key_env names from LLM_BOT_CONFIGS.
    - Raises a RuntimeError listing any missing variables.
    """
    # Load from .env but do not override variables already set in the environment
    load_dotenv(override=False)

    required_env_vars = {cfg["api_key_env"] for cfg in LLM_BOT_CONFIGS.values() if "api_key_env" in cfg}

    missing = []
    for var in sorted(required_env_vars):
        val = os.getenv(var)
        if not val:
            missing.append(var)

    if missing:
        raise RuntimeError(
            "Missing required API key environment variables: "
            + ", ".join(missing)
            + ". Please add them to your .env file or export them in your environment."
        )


class LLMBot:

    def __init__(self, llm, subject, name=None):
        if llm not in LLM_BOT_CONFIGS:
            raise ValueError(f"Unknown LLM provider '{llm}'. Available: {', '.join(LLM_BOT_CONFIGS.keys())}")
        load_api_key()
        self.configuration = LLM_BOT_CONFIGS[llm]
        self.subject = subject
        api_key = os.getenv(self.configuration["api_key_env"])
        self.llm = llm
        self.name = name or self.configuration["name"]
        self.system_prompt = \
            (f"You are {self.name}, a person talking to other persons in one room discussing the {subject}.\
                If you are first to speak about the {subject} please describe it in detail to other people and express your opinion.\
                Talk politely and without any prejudices. Be short as other people also would like to express own opinion. If other people already speak about the {subject} \
                please make a comment adding some value to the conversation.")
        base_url = self.configuration.get("base_url")
        if self.llm == "claude" and not base_url:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = OpenAI(api_key=api_key, base_url=base_url)

    def get_response(self, prompt):
        if self.llm == "claude":
            # Anthropic API: system prompt is provided separately; messages contain user/assistant turns
            messages = [
                {"role": "user", "content": prompt},
            ]
            response = self.client.messages.create(
                model=self.configuration["model"],
                max_tokens=200,
                temperature=0.7,
                system=self.system_prompt,
                messages=messages,
            )
            return response.content[0].text
        else:
            # OpenAI-compatible chat completion API (OpenAI, DeepSeek, Gemini via OpenAI shim)
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.configuration["model"],
                messages=messages,
            )
            return response.choices[0].message.content
