# src/llm/llm_factory.py

"""
Factory for creating LLM clients
"""

from llm.open_api.openai_client import OpenAIClient
from llm.llama.llama_client import LlamaClient


class LLMFactory:
    """Factory for creating LLM clients."""
    
    @staticmethod
    def get_providers():
        """
        Get available LLM providers.
        
        Returns:
            dict: Dictionary of provider name to display name
        """
        return {
            "openai": "OpenAI",
            "llama": "Llama (Local)"
        }
    
    @staticmethod
    def create_client(provider_name):
        """
        Create an LLM client based on provider name.
        
        Args:
            provider_name: The name of the provider
            
        Returns:
            BaseLLMClient: The initialized LLM client
        """
        if provider_name == "openai":
            return OpenAIClient().initialize()
        elif provider_name == "llama":
            return LlamaClient().initialize()
        else:
            raise ValueError(f"Unknown provider: {provider_name}")