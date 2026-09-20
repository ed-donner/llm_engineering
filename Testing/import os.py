import os
from dotenv import load_dotenv

# load_dotenv(override=True)

api_key = os.getenv("FAVORITE_FRUIT")
print(api_key)