
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ModelConfig:
    sentiment_model:     str = "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis"
    embedding_model:     str = "sentence-transformers/all-MiniLM-L6-v2"
    claude_model:        str = "anthropic/claude-sonnet-4-5"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    gpt_model:           str = "gpt-4o"
    claude_max_tokens:   int = 2048
    gpt_max_tokens:      int = 1024


@dataclass(frozen=True)
class NewsConfig:
    finnhub_base_url:  str       = "https://finnhub.io/api/v1"
    
    news_categories:   list      = field(default_factory=lambda: ["forex", "merger"])
    news_limit:        int       = 20        
    interval_minutes:  int       = 10


@dataclass(frozen=True)
class VectorStoreConfig:
    persist_directory: str = "./chroma_db"
    collection_name:   str = "financial_news"
    n_results:         int = 5


@dataclass(frozen=True)
class PushoverConfig:
    api_url: str = "https://api.pushover.net/1/messages.json"


@dataclass(frozen=True)
class AppConfig:
    models:       ModelConfig       = field(default_factory=ModelConfig)
    news:         NewsConfig        = field(default_factory=NewsConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    pushover:     PushoverConfig    = field(default_factory=PushoverConfig)

    openai_api_key:      Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openrouter_api_key:  Optional[str] = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY"))
    finnhub_api_key:     Optional[str] = field(default_factory=lambda: os.getenv("FINNHUB_API_KEY"))
    pushover_user_key:   Optional[str] = field(default_factory=lambda: os.getenv("PUSHOVER_USER_KEY"))
    pushover_app_token:  Optional[str] = field(default_factory=lambda: os.getenv("PUSHOVER_APP_TOKEN"))

    server_port: int  = 7860
    share:       bool = False

    def validate(self) -> None:
        missing = [
            k for k, v in {
                "OPENAI_API_KEY":     self.openai_api_key,
                "OPENROUTER_API_KEY": self.openrouter_api_key,
                "FINNHUB_API_KEY":    self.finnhub_api_key,
                "PUSHOVER_USER_KEY":  self.pushover_user_key,
                "PUSHOVER_APP_TOKEN": self.pushover_app_token,
            }.items() if not v
        ]
        if missing:
            raise EnvironmentError(
                "Missing required environment variables:\n  " + "\n  ".join(missing)
            )


APP_CONFIG = AppConfig(
    models=ModelConfig(),
    news=NewsConfig(),
    vector_store=VectorStoreConfig(),
    pushover=PushoverConfig(),
)
