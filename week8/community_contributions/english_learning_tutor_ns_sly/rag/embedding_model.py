import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')



class EmbeddingModel:

    def __init__(self):

        self.client = OpenAI()

    def embed(self, texts):

        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )

        return [np.array(e.embedding) for e in response.data]