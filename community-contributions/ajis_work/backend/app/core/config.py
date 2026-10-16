import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
    
    FRONTEND_ORIGINS = os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000"
    ).split(",")


settings = Settings()
