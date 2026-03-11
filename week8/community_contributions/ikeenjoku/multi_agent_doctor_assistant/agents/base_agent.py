"""
Base Agent Class for Multi-Agent Medical Assistant
"""

from abc import ABC, abstractmethod
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI


class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system"""

    def __init__(self, vectorstore: Chroma, llm: ChatOpenAI):
        """
        Initialize base agent

        Args:
            vectorstore: Chroma vector database
            llm: Language model for generation
        """
        self.vectorstore = vectorstore
        self.llm = llm

    @abstractmethod
    def process(self, query: str, **kwargs):
        """
        Process a query and return results

        Args:
            query: The input query/question
            **kwargs: Additional arguments specific to each agent

        Returns:
            dict: Agent-specific results
        """
        pass
