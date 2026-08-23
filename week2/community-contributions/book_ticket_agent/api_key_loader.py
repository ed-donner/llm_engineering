import os

from dotenv import load_dotenv

KEY_CONFIGS = {
    "gpt": {
        "id": "gpt",
        "api_key_env": "OPENAI_API_KEY",
    },
    "claude": {
        "id": "claude",
        "api_key_env": "ANTHROPIC_API_KEY",
    },
    "gemini": {
        "id": "gemini",
        "api_key_env": "GOOGLE_API_KEY",
    },
    "openai": {
        "id": "openai",
        "api_key_env": "OPENAI_API_KEY",
    },
    "deepseek": {
        "id": "deepseek",
        "api_key_env": "DEEPSEEK_API_KEY"
    },
    "amadeus_client_id": {
        "id": "client_id",
        "api_key_env": "AMADEUS_CLIENT_ID"
    },
    "amadeus_client_secret": {
        "id": "client_secret",
        "api_key_env": "AMADEUS_CLIENT_SECRET"
    },
    "google_map": {
        "id": "google_map_api_key",
        "api_key_env": "GOOGLE_MAP_API_KEY"
    }
}

class ApiKeyLoader:
    def __init__(self):
        load_dotenv(override=False)

        required_env_vars = {cfg["api_key_env"] for cfg in KEY_CONFIGS.values() if "api_key_env" in cfg}

        self.missing = [var for var in sorted(required_env_vars) if not os.getenv(var)]

        if self.missing:
            raise RuntimeError(
                "Missing required API key environment variables: "
                + ", ".join(self.missing)
                + ". Please add them to your .env file or export them in your environment."
            )
        
        self.keys = {
            cfg["id"]: os.getenv(cfg["api_key_env"])
            for cfg in KEY_CONFIGS.values()
            if os.getenv(cfg["api_key_env"])
        }
                
    def get(self, key):
        return self.keys.get(key)