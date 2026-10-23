
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]

class SystemSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    GROQ_API_KEY: str

    DB_PATH : Path = PROJECT_ROOT / 'assets' / "dbs"  / "products.db"
    CSV_PATH: Path = PROJECT_ROOT / 'assets' / "dbs" / "products.csv"

    AUDIO_PATH: Path = PROJECT_ROOT / 'assets' / 'request_metadata' / 'audio.wav'
    PLOTS_PATH: Path = PROJECT_ROOT / 'assets' / 'request_metadata'


    PROJECT_ROOT: Path = PROJECT_ROOT

    # -- LLMs
    TEXT_TO_TEXT_LLM: str = "openai/gpt-oss-120b"
    AUDIO_TO_TEXT_LLM: str = "whisper-large-v3"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    ORCHESTRATOR_MAX_STEPS: int = 6

def get_system_settings() -> SystemSettings:
    return SystemSettings()
