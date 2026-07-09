from typing import Dict, Type
from src.models import (
    BaseProvider,
    OpenAIProvider,
    OpenRouterProvider,
    AnthropicProvider,
    GoogleProvider,
    OllamaProvider
)

class ProviderFactory:
    _registry: Dict[str, Type[BaseProvider]] = {
        "OpenAI": OpenAIProvider,
        "OpenRouter": OpenRouterProvider,
        "Anthropic": AnthropicProvider,
        "Google": GoogleProvider,
        "Ollama": OllamaProvider
    }

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseProvider]):
        """
        Dynamically register a new provider implementation.
        """
        cls._registry[name] = provider_class

    @classmethod
    def get_provider(cls, name: str, **kwargs) -> BaseProvider:
        """
        Instantiate the registered provider class by name.
        """
        if name not in cls._registry:
            raise ValueError(f"Unknown provider '{name}'. Registered: {list(cls._registry.keys())}")
        
        provider_class = cls._registry[name]
        return provider_class(**kwargs)
