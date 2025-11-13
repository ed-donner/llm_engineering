import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
#############
# PARAMETER #
#############

MAX_TOKENS = 1000

############
# API KEYS #
############

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

############
# API URLS #
############

groq_url = "https://api.groq.com/openai/v1"

###########
# CLIENTS #
###########

groq_client     = AsyncOpenAI(base_url=groq_url, api_key=groq_api_key)
openai_client   = AsyncOpenAI()


# Clients models and client dictionary
models = [
    "gpt-4o-mini",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
]

clients = {
    "gpt-4o-mini": openai_client,  # OpenAI model                $0.15/$0.60
    "meta-llama/llama-4-scout-17b-16e-instruct": groq_client,  # Groq Llama model            $0.11/$0.34
    "openai/gpt-oss-20b": groq_client,  # Groq GPT OSS 20B - cheaper  $0.075/$0.30
    "openai/gpt-oss-120b": groq_client,  # Groq GPT OSS 120B powerful  $0.15/$0.60
}

