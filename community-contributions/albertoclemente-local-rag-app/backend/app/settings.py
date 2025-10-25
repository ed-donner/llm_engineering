"""
Application settings and configuration management.
Supports Eco/Balanced/Performance profiles and environment-based configuration.
"""

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Profile(str, Enum):
    """Performance profiles for resource management"""
    ECO = "eco"
    BALANCED = "balanced"
    PERFORMANCE = "performance"


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Server configuration
    host: str = Field(default="127.0.0.1", env="RAG_HOST")
    port: int = Field(default=8000, env="RAG_PORT")
    debug: bool = Field(default=False, env="RAG_DEBUG")
    
    # Performance profile
    profile: Profile = Field(default=Profile.BALANCED, env="RAG_PROFILE")
    
    # Data directories
    data_dir: str = Field(default="~/RAGApp", env="RAG_DATA_DIR")
    
    # External services
    qdrant_url: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    qdrant_path: Optional[str] = Field(default=None, env="QDRANT_PATH")  # For local file-based Qdrant
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    
    # Model settings
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="RAG_EMBEDDING_MODEL")
    llm_model: str = Field(default="qwen2.5:7b-instruct", env="RAG_LLM_MODEL")
    
    # RAG parameters (defaults based on profile)
    chunk_size: int = Field(default=800, env="RAG_CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="RAG_CHUNK_OVERLAP")
    max_context_tokens: int = Field(default=4000, env="RAG_MAX_CONTEXT_TOKENS")
    
    # Security
    encryption_key: Optional[str] = Field(default=None, env="RAG_ENCRYPTION_KEY")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"  # Allow extra environment variables
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Expand user directory
        self.data_dir = str(Path(self.data_dir).expanduser())
        
        # Apply profile-specific settings
        self._apply_profile_settings()
    
    def _apply_profile_settings(self):
        """Apply performance profile specific settings"""
        if self.profile == Profile.ECO:
            # Conservative settings for battery life
            if "RAG_CHUNK_SIZE" not in os.environ:
                self.chunk_size = 600
            if "RAG_MAX_CONTEXT_TOKENS" not in os.environ:
                self.max_context_tokens = 2000
        elif self.profile == Profile.PERFORMANCE:
            # Aggressive settings for accuracy
            if "RAG_CHUNK_SIZE" not in os.environ:
                self.chunk_size = 1000
            if "RAG_MAX_CONTEXT_TOKENS" not in os.environ:
                self.max_context_tokens = 8000
        # BALANCED uses the defaults
    
    @property
    def storage_path(self) -> str:
        """Get the storage path (alias for data_dir)."""
        return self.data_dir
    
    @property
    def performance_profile(self) -> str:
        """Get the performance profile as string."""
        return self.profile.value
    
    @property
    def qdrant_data_dir(self) -> str:
        """Get the Qdrant data directory."""
        return os.path.join(self.data_dir, "qdrant_data")
    
    @property
    def config_dir(self) -> str:
        return os.path.join(self.data_dir, "config")
    
    @property
    def logs_dir(self) -> str:
        return os.path.join(self.data_dir, "logs")
    
    @property
    def models_dir(self) -> str:
        return os.path.join(self.data_dir, "models")
    
    @property
    def library_raw_dir(self) -> str:
        return os.path.join(self.data_dir, "library", "raw")
    
    @property
    def library_parsed_dir(self) -> str:
        return os.path.join(self.data_dir, "library", "parsed")
    
    @property
    def library_indices_dir(self) -> str:
        return os.path.join(self.data_dir, "library", "indices")
    
    @property
    def exports_dir(self) -> str:
        return os.path.join(self.data_dir, "exports")
    
    @property
    def eval_dir(self) -> str:
        return os.path.join(self.data_dir, "eval")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
