"""
Base Agent class - Foundation for all specialized agents
"""
from abc import ABC, abstractmethod
import logging
from typing import Optional, Dict, Any
from utils.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, name: str, llm_client: Optional[OllamaClient] = None, 
                 model: str = "llama3.2"):
        """
        Initialize base agent
        
        Args:
            name: Agent name for logging
            llm_client: Shared Ollama client (creates new one if None)
            model: Ollama model to use
        """
        self.name = name
        self.model = model
        
        # Use shared client or create new one
        if llm_client is None:
            self.llm = OllamaClient(model=model)
            logger.info(f"{self.name} initialized with new LLM client (model: {model})")
        else:
            self.llm = llm_client
            logger.info(f"{self.name} initialized with shared LLM client (model: {model})")
    
    def generate(self, prompt: str, system: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """
        Generate text using the LLM
        
        Args:
            prompt: User prompt
            system: System message (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        logger.info(f"{self.name} generating response")
        response = self.llm.generate(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens
        )
        logger.debug(f"{self.name} generated {len(response)} characters")
        return response
    
    def chat(self, messages: list, temperature: float = 0.7, 
             max_tokens: int = 2048) -> str:
        """
        Chat completion with message history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        logger.info(f"{self.name} processing chat with {len(messages)} messages")
        response = self.llm.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        logger.debug(f"{self.name} generated {len(response)} characters")
        return response
    
    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """
        Main processing method - must be implemented by subclasses
        
        Each agent implements its specialized logic here
        """
        pass
    
    def __str__(self):
        return f"{self.name} (model: {self.model})"
