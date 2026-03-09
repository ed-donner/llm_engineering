import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL_RELEVANCE = "deepseek/deepseek-chat"
MODEL_INSIGHT = "meta-llama/llama-3.1-70b-instruct"

VECTOR_DB_PATH = "./vectorstore/chroma_db"