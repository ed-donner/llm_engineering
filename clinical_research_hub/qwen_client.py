#!/usr/bin/env python3
"""
Qwen OpenRouter API Client for Clinical Research Pipeline
Provides a compatible interface with OpenAI client for seamless migration.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any

# Load environment variables
load_dotenv()


class QwenOpenRouterClient:
    """Qwen API client that mimics OpenAI client interface for easy migration."""
    
    def __init__(self, api_key: str = None):
        """Initialize the Qwen API client with OpenRouter credentials.
        
        Args:
            api_key: OpenRouter API key (if not provided, will use OPENROUTER_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found. Please set it as an environment variable "
                "or pass it as api_key parameter."
            )
        
        # Initialize OpenAI client with OpenRouter endpoint
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        
        # The specific Qwen model available on OpenRouter
        self.model_name = "qwen/qwen-2.5-72b-instruct"  # Updated to a more capable model
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
    @property
    def chat(self):
        """Provide chat interface compatible with OpenAI client."""
        return self
    
    @property
    def completions(self):
        """Provide completions interface compatible with OpenAI client."""
        return self
    
    def create(self, model: str = None, messages: List[Dict[str, str]] = None, 
               max_tokens: int = 1000, temperature: float = 0.3, **kwargs):
        """
        Create a chat completion using Qwen model via OpenRouter.
        Compatible with OpenAI client interface.
        
        Args:
            model: Model name (will use Qwen regardless)
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional parameters
            
        Returns:
            Response object compatible with OpenAI format
        """
        try:
            # Use our Qwen model regardless of what model is requested
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Qwen OpenRouter API request failed: {e}")
            raise Exception(f"Qwen API request failed: {e}")
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3):
        """
        Generate text using the Qwen model via OpenRouter API.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            str: Generated text
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            
            response = self.create(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Qwen text generation failed: {e}")
            raise Exception(f"Qwen text generation failed: {e}")
    
    def get_model_info(self):
        """Get information about the current Qwen model."""
        return {
            "model": self.model_name,
            "provider": "OpenRouter",
            "context_length": "128k tokens",
            "license": "Apache-2",
            "cost": "Competitive pricing via OpenRouter"
        }


# For backward compatibility, create an OpenAI-like interface
class QwenOpenAI:
    """OpenAI-compatible wrapper for Qwen client."""
    
    def __init__(self, api_key: str):
        """Initialize with OpenRouter API key instead of OpenAI key."""
        self.qwen_client = QwenOpenRouterClient(api_key)
    
    @property
    def chat(self):
        """Provide chat interface."""
        return self.qwen_client
