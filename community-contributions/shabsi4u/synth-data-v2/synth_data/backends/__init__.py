"""
Backend implementations for synthetic data generation.

This package contains abstract base classes and concrete implementations
for various LLM backends (HuggingFace, OpenAI, Ollama, etc.).
"""

from .base import ModelBackend, GenerationParams, GenerationResult
from .huggingface_api import HuggingFaceAPIBackend

__all__ = [
    "ModelBackend",
    "GenerationParams",
    "GenerationResult",
    "HuggingFaceAPIBackend",
]
