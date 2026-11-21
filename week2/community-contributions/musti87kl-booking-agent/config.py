#load keys from .env into memory; the OpenAI client reads key by itself.
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv(override=True)
#Model choice
MODEL="gpt-6-luna"  
#the courier
openai = OpenAI()  # reads OPENAI_API_KEY by itself