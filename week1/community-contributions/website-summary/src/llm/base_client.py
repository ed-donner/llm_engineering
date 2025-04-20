# src/llm/base_client.py

"""
Base LLM client interface for the Website Summary Tool
"""

from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def initialize(self):
        """Initialize the LLM client."""
        pass
    
    @abstractmethod
    def validate_credentials(self):
        """
        Validate API credentials.
        
        Returns:
            tuple: (is_valid, message)
        """
        pass
    
    @abstractmethod
    def test_connection(self, test_message):
        """
        Send a test message to verify API connectivity.
        
        Args:
            test_message: The message to send
            
        Returns:
            str: The response from the model
        """
        pass
    
    @abstractmethod
    def format_messages(self, messages):
        """
        Format messages according to the provider's requirements.
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            The properly formatted messages for this specific provider
        """
        pass
    
    @abstractmethod
    def generate_content(self, messages, model=None, **kwargs):
        """
        Generate content from the LLM.
        
        Args:
            messages: The messages to send
            model: The model to use for generation
            **kwargs: Additional provider-specific parameters
            
        Returns:
            str: The generated content
        """
        pass
    
    @abstractmethod
    def get_available_models(self):
        """
        Get available models from this provider.
        
        Returns:
            list: Available model names
        """
        pass