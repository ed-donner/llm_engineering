import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
import ollama
from agents.agent import Agent

class SpecialistAgentWrapper(Agent):
    """
    An Agent that runs our fine-tuned LLM locally using Ollama
    Replaces the Modal-based SpecialistAgent
    """

    name = "Specialist Agent"
    color = Agent.RED
    MODEL = "llama3.2:3b-instruct-q4_0"
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def __init__(self):
        """
        Set up this Agent by creating an Ollama client
        """
        self.log("Specialist Agent is initializing - connecting to Ollama")
        try:
            self.client = ollama.Client(host=self.OLLAMA_HOST)
            # Test connection
            self.client.list()  # This will fail if Ollama is not available
            self.log("Specialist Agent is ready - Ollama connection successful")
            self.ollama_available = True
        except Exception as e:
            self.log(f"Ollama connection failed: {str(e)}")
            self.log("Specialist Agent is ready - using fallback mode")
            self.ollama_available = False
        
    def price(self, description: str) -> float:
        """
        Make a call to Ollama to return the estimate of the price of this item
        """
        self.log("Specialist Agent is calling Ollama for price estimation")
        
        # If Ollama is not available, use fallback immediately
        if not self.ollama_available:
            self.log("Ollama not available, using fallback pricing")
            fallback_price = self._fallback_pricing(description)
            self.log(f"Fallback price: ${fallback_price:.2f}")
            return fallback_price
        
        try:
            # Test connection first
            self.log(f"Connecting to Ollama at {self.OLLAMA_HOST}")
            
            response = self.client.chat(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a product pricing expert. Estimate the price of products based on their descriptions. Respond with only a number representing the estimated price in dollars."
                    },
                    {
                        "role": "user", 
                        "content": f"Estimate the price of this product: {description}"
                    }
                ]
            )
            
            # Extract price from response
            price_text = response['message']['content'].strip()
            self.log(f"Raw response from Ollama: {price_text}")
            
            # Try to extract numeric value
            import re
            price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
            if price_match:
                price = float(price_match.group())
            else:
                self.log(f"Could not extract price from response: {price_text}")
                price = 0.0
                
            self.log(f"Specialist Agent completed - predicting ${price:.2f}")
            return price
            
        except Exception as e:
            self.log(f"Error calling Ollama: {str(e)}")
            self.log(f"Ollama host: {self.OLLAMA_HOST}")
            self.log(f"Model: {self.MODEL}")
            
            # Fallback: simple keyword-based pricing for testing
            self.log("Using fallback pricing logic")
            fallback_price = self._fallback_pricing(description)
            self.log(f"Fallback price: ${fallback_price:.2f}")
            return fallback_price
    
    def _fallback_pricing(self, description: str) -> float:
        """
        Simple fallback pricing based on keywords for testing
        """
        description_lower = description.lower()
        
        # Basic keyword-based pricing
        if any(word in description_lower for word in ['iphone', 'iphone 15', 'pro max']):
            return 1200.0
        elif any(word in description_lower for word in ['macbook', 'macbook pro', 'm3']):
            return 2000.0
        elif any(word in description_lower for word in ['samsung', 'galaxy', 's24']):
            return 1000.0
        elif any(word in description_lower for word in ['sony', 'headphones', 'wh-1000xm5']):
            return 400.0
        elif any(word in description_lower for word in ['laptop', 'computer']):
            return 800.0
        elif any(word in description_lower for word in ['phone', 'smartphone']):
            return 600.0
        elif any(word in description_lower for word in ['tablet', 'ipad']):
            return 500.0
        else:
            return 100.0  # Default fallback price
