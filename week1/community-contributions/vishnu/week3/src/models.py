import os
import time
import json
import logging
from typing import List, Dict, Any, Iterator, Tuple

logger = logging.getLogger("Questher.models")
logging.basicConfig(level=logging.INFO)

# Mappings from direct vendor model IDs to OpenRouter model IDs for unified fallbacks
OPENROUTER_FALLBACK_MAPPING = {
    # Anthropic
    "claude-3-5-sonnet-20241022": "anthropic/claude-3.5-sonnet",
    "claude-3-opus-20240229": "anthropic/claude-3-opus",
    # Google
    "gemini-1.5-flash": "google/gemini-flash-1.5",
    "gemini-1.5-pro": "google/gemini-pro-1.5",
}

# Base class for all providers
class BaseProvider:
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url

    def generate(self, model_id: str, prompt: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> Tuple[str, float]:
        """
        Generate completion. Returns (content, latency).
        """
        raise NotImplementedError

    def generate_stream(self, model_id: str, prompt: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> Iterator[str]:
        """
        Generate streaming completion.
        """
        raise NotImplementedError

    def _prepare_messages(self, prompt: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            for item in history:
                messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})
        messages.append({"role": "user", "content": prompt})
        return messages


# OpenAI Provider
class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str = None):
        super().__init__(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        from openai import OpenAI
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, model_id: str, prompt: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> Tuple[str, float]:
        messages = self._prepare_messages(prompt, system_prompt, history)
        start_time = time.time()
        response = self.client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0.2
        )
        latency = time.time() - start_time
        return response.choices[0].message.content or "", latency

    def generate_stream(self, model_id: str, prompt: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> Iterator[str]:
        messages = self._prepare_messages(prompt, system_prompt, history)
        stream = self.client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0.2,
            stream=True
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# OpenRouter Provider
class OpenRouterProvider(BaseProvider):
    def __init__(self, api_key: str = None):
        super().__init__(
            api_key=api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        from openai import OpenAI
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate(self, model_id: str, prompt: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> Tuple[str, float]:
        messages = self._prepare_messages(prompt, system_prompt, history)
        start_time = time.time()
        response = self.client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0.2
        )
        latency = time.time() - start_time
        return response.choices[0].message.content or "", latency

    def generate_stream(self, model_id: str, prompt: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> Iterator[str]:
        messages = self._prepare_messages(prompt, system_prompt, history)
        stream = self.client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0.2,
            stream=True
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# Anthropic Provider (Claude)
class AnthropicProvider(BaseProvider):
    def __init__(self, api_key: str = None):
        super().__init__(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        # Fall back to OpenRouter representation if Anthropic key is not available
        self.use_openrouter_fallback = not self.api_key
        if self.use_openrouter_fallback:
            self.fallback_provider = OpenRouterProvider()
        else:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)

    def generate(self, model_id: str, prompt: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> Tuple[str, float]:
        if self.use_openrouter_fallback:
            # Map Anthropic ID to OpenRouter format using our fallback mapping dictionary
            or_model = OPENROUTER_FALLBACK_MAPPING.get(model_id, f"anthropic/{model_id}" if "/" not in model_id else model_id)
            return self.fallback_provider.generate(or_model, prompt, system_prompt, history)

        # Standard Anthropic invocation
        messages = []
        if history:
            for item in history:
                messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        start_time = time.time()
        kwargs = {
            "model": model_id,
            "max_tokens": 1024,
            "messages": messages,
            "temperature": 0.2
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)
        latency = time.time() - start_time
        return response.content[0].text or "", latency

    def generate_stream(self, model_id: str, prompt: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> Iterator[str]:
        if self.use_openrouter_fallback:
            or_model = OPENROUTER_FALLBACK_MAPPING.get(model_id, f"anthropic/{model_id}" if "/" not in model_id else model_id)
            yield from self.fallback_provider.generate_stream(or_model, prompt, system_prompt, history)
            return

        messages = []
        if history:
            for item in history:
                messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": model_id,
            "max_tokens": 1024,
            "messages": messages,
            "temperature": 0.2
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text


# Google Provider (Gemini)
class GoogleProvider(BaseProvider):
    def __init__(self, api_key: str = None):
        super().__init__(api_key=api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        self.use_openrouter_fallback = not self.api_key
        if self.use_openrouter_fallback:
            self.fallback_provider = OpenRouterProvider()
        else:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai

    def generate(self, model_id: str, prompt: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> Tuple[str, float]:
        if self.use_openrouter_fallback:
            or_model = OPENROUTER_FALLBACK_MAPPING.get(model_id, f"google/{model_id}" if "/" not in model_id else model_id)
            return self.fallback_provider.generate(or_model, prompt, system_prompt, history)

        # Direct Google GenerativeAI call
        start_time = time.time()
        # Clean model name to make sure it matches direct GenAI naming
        clean_model = model_id.split("/")[-1] if "/" in model_id else model_id
        
        system_instruction = system_prompt if system_prompt else None
        model = self.genai.GenerativeModel(clean_model, system_instruction=system_instruction)
        
        # Format history for google chat api
        chat = model.start_chat(history=[])
        if history:
            for item in history:
                # Mock adding to chat history
                pass
        
        response = chat.send_message(prompt)
        latency = time.time() - start_time
        return response.text, latency

    def generate_stream(self, model_id: str, prompt: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> Iterator[str]:
        if self.use_openrouter_fallback:
            or_model = OPENROUTER_FALLBACK_MAPPING.get(model_id, f"google/{model_id}" if "/" not in model_id else model_id)
            yield from self.fallback_provider.generate_stream(or_model, prompt, system_prompt, history)
            return

        clean_model = model_id.split("/")[-1] if "/" in model_id else model_id
        system_instruction = system_prompt if system_prompt else None
        model = self.genai.GenerativeModel(clean_model, system_instruction=system_instruction)
        
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text


# Ollama Provider (Local)
class OllamaProvider(BaseProvider):
    def __init__(self, base_url: str = "http://localhost:11434/v1"):
        super().__init__(api_key="ollama", base_url=base_url)
        from openai import OpenAI
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate(self, model_id: str, prompt: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> Tuple[str, float]:
        messages = self._prepare_messages(prompt, system_prompt, history)
        start_time = time.time()
        try:
            response = self.client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=0.2
            )
            latency = time.time() - start_time
            return response.choices[0].message.content or "", latency
        except Exception as e:
            logger.error(f"Ollama local connection error: {e}")
            raise ConnectionError(f"Unable to connect to Ollama local server: {e}")

    def generate_stream(self, model_id: str, prompt: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> Iterator[str]:
        messages = self._prepare_messages(prompt, system_prompt, history)
        try:
            stream = self.client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=0.2,
                stream=True
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Ollama local connection error: {e}")
            raise ConnectionError(f"Unable to connect to Ollama local server: {e}")


# Model Manager and Analytics logger
class ModelManager:
    # Model catalog configuration
    PROVIDERS_CATALOG = {
        "OpenRouter": [
            "google/gemini-2.5-pro",
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "meta-llama/llama-3.2-3b-instruct"
        ],
        "OpenAI": [
            "gpt-4o-mini",
            "gpt-4o"
        ],
        "Anthropic": [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229"
        ],
        "Google": [
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ],
        "Ollama": [
            "llama3.2",
            "llama3",
            "mistral",
            "phi3"
        ]
    }

    ANALYTICS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analytics.json")

    @classmethod
    def get_available_models(cls, provider: str) -> List[str]:
        return cls.PROVIDERS_CATALOG.get(provider, [])

    @classmethod
    def log_interaction(cls, provider: str, model: str, latency: float, success: bool, error: str = ""):
        """
        Persist analytics of model requests to analytics.json.
        """
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "provider": provider,
            "model": model,
            "latency": round(latency, 3),
            "success": success,
            "error": error
        }

        try:
            logs = []
            if os.path.exists(cls.ANALYTICS_FILE):
                with open(cls.ANALYTICS_FILE, "r", encoding="utf-8") as f:
                    try:
                        logs = json.load(f)
                    except Exception:
                        logs = []
            
            logs.append(log_entry)
            
            with open(cls.ANALYTICS_FILE, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to log interaction to analytics file: {e}")

    @classmethod
    def get_analytics(cls) -> List[Dict[str, Any]]:
        if not os.path.exists(cls.ANALYTICS_FILE):
            return []
        try:
            with open(cls.ANALYTICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @classmethod
    def reset_analytics(cls):
        try:
            with open(cls.ANALYTICS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
        except Exception as e:
            logger.error(f"Failed to reset analytics: {e}")
