# src/llm/open_api/openai_client.py

"""
OpenAI API interaction for the Website Summary Tool
"""

import os
from openai import OpenAI
from llm.base_client import BaseLLMClient
from helper.env_utils import find_and_load_env_file
from llm.helper.validation_utils import LLMValidator


class OpenAIClient(BaseLLMClient):
    """Client for the OpenAI API."""
    
    def __init__(self):
        """Initialize the OpenAI client."""
        self.api_key = None
        self.client = None
        self.available_models = [
            "gpt-4o-mini",
            "gpt-4o", 
            "gpt-3.5-turbo"
        ]
        self.default_model = "gpt-4o-mini"
    
    def initialize(self):
        """Initialize the OpenAI client."""
        # Load .env file and set API key
        find_and_load_env_file()
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        if self.api_key:
            print("✅ OPENAI_API_KEY found in environment variables")
            self.client = OpenAI(api_key=self.api_key)
        else:
            print("❌ OPENAI_API_KEY not found in environment variables")
            # Try alternative approach as seen in example_usage.ipynb
            print("Attempting alternative method to find OpenAI API key...")
            # Create client without explicit key - it may find it elsewhere
            self.client = OpenAI()
            
        return self
    
    def validate_credentials(self):
        """
        Validate that the API key exists and has correct formatting.
        
        Returns:
            tuple: (is_valid, message)
        """
        return LLMValidator.validate_openai_key(self.api_key)
    
    def test_connection(self, test_message="Hello, GPT! This is a test message."):
        """
        Send a test message to verify API connectivity.
        
        Args:
            test_message: The message to send
            
        Returns:
            str: The response from the model
        """
        try:
            response = self.client.chat.completions.create(
                model=self.default_model, 
                messages=[
                    {"role": "user", "content": test_message}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error connecting to OpenAI API: {str(e)}"
    
    def format_messages(self, messages):
        """
        Format messages for OpenAI API.
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            list: The messages formatted for OpenAI
        """
        # OpenAI already uses the format we're using, so we can return as-is
        return messages

    def generate_content(self, messages, model=None, **kwargs):
        """
        Generate content from OpenAI.
        
        Args:
            messages: The messages to send
            model: The model to use for generation
            **kwargs: Additional OpenAI-specific parameters
            
        Returns:
            str: The generated content
        """
        model = model or self.default_model
        formatted_messages = self.format_messages(messages)
        
        response = self.client.chat.completions.create(
            model=model,
            messages=formatted_messages,
            **kwargs
        )
        return response.choices[0].message.content
    
    def get_available_models(self):
        """
        Get available models from OpenAI.
        
        Returns:
            list: Available model names
        """
        return self.available_models