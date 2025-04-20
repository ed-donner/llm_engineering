# src/llm/llama/llama_client.py

"""
Llama API interaction for the Website Summary Tool
"""

import os
import ollama
from llm.base_client import BaseLLMClient
from helper.env_utils import find_and_load_env_file
from llm.helper.validation_utils import LLMValidator


class LlamaClient(BaseLLMClient):
    """Client for the Llama API (locally hosted through Ollama)."""
    
    def __init__(self):
        """Initialize the Llama client."""
        self.api_base = None
        self.available_models = ["llama3.2:latest"]
        self.default_model = "llama3.2:latest"
    
    def initialize(self):
        """Initialize the Llama client by loading config."""
        # Load .env file and set API URL
        find_and_load_env_file()
        
        # Get the API base URL from environment variables
        self.api_base = os.getenv('LLAMA_API_URL', 'http://localhost:11434')
        print(f"LLAMA_API_URL: {self.api_base}")
        
        # Set the host URL for ollama client
        ollama.host = self.api_base
        return self
    
    def validate_credentials(self):
        """
        Validate that the Llama API is accessible.
        
        Returns:
            tuple: (is_valid, message)
        """
        if not self.api_base:
            return False, "No Llama API URL found - please add LLAMA_API_URL to your .env file"
        
        try:
            # Get the list of models from Ollama
            models_data = ollama.list()
            
            # Print the raw models data for debugging
            print(f"Raw Ollama models data: {models_data}")
            
            # Validate models data contains our target model
            found_model, is_valid, message = LLMValidator.validate_ollama_models(
                models_data, self.default_model
            )
            
            if is_valid:
                self.default_model = found_model  # Update with the exact model name
                return True, f"Ollama API connection successful! Found model {self.default_model}"
            else:
                return False, f"Connected to Ollama API but no llama3.x model found. Please run 'ollama pull llama3.2'"
        except Exception as e:
            return False, f"Error connecting to Ollama API: {str(e)}"
    
    def test_connection(self, test_message="Hello, this is a test message."):
        """
        Send a test message to verify API connectivity.
        
        Args:
            test_message: The message to send
            
        Returns:
            str: The response from the model
        """
        try:
            response = ollama.chat(
                model=self.default_model,
                messages=[{"role": "user", "content": test_message}]
            )
            return response["message"]["content"]
        except Exception as e:
            return f"Error connecting to Ollama API: {str(e)}"
    
    def format_messages(self, messages):
        """
        Format messages for Llama API.
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            list: A formatted messages list for Ollama
        """
        # The ollama.chat API accepts messages in the same format as OpenAI
        return messages

    def generate_content(self, messages, model=None, **kwargs):
        """
        Generate content from Llama.
        
        Args:
            messages: The messages to send
            model: The model to use for generation
            **kwargs: Additional Llama-specific parameters
            
        Returns:
            str: The generated content
        """
        model = model or self.default_model
        formatted_messages = self.format_messages(messages)
        
        try:
            # Create options dictionary for additional parameters
            options = {}
            if "temperature" in kwargs:
                options["temperature"] = kwargs["temperature"]
            
            # Call ollama.chat with our messages and options
            response = ollama.chat(
                model=model,
                messages=formatted_messages,
                options=options
            )
            
            return response["message"]["content"]
        except Exception as e:
            if "connection" in str(e).lower():
                raise Exception(f"Could not connect to Ollama at {self.api_base}. Is the Ollama server running?")
            else:
                raise Exception(f"Error with Ollama API: {str(e)}")
    
    def get_available_models(self):
        """
        Get available models from Ollama.
        
        Returns:
            list: Available model names
        """
        try:
            models_data = ollama.list()
            
            # Extract model names based on response format
            if hasattr(models_data, 'models'):
                model_names = [model.model for model in models_data.models if hasattr(model, 'model')]
            elif isinstance(models_data, dict) and 'models' in models_data:
                model_names = [model.get('name') for model in models_data.get('models', [])]
            else:
                model_names = []
            
            # Filter for our specific model
            filtered_models = [name for name in model_names if self.default_model.split(':')[0] in name]
            return filtered_models if filtered_models else self.available_models
        except Exception as e:
            print(f"Error getting available models: {str(e)}")
            return self.available_models