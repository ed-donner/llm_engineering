# imports

import os
import re
import math
import json
from typing import List
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from datasets import load_dataset
import chromadb
from items import Item
from testing import Tester

class FrontierAgent:

    MODEL = "gpt-4o-mini"
    
    def __init__(self, collection):
        self.openai = OpenAI()
        self.collection = collection
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def make_context(self, similars: List[str], prices: List[float]):
        message = "To provide some context, here are some other items that might be similar to the item you need to estimate.\n\n"
        for similar, price in zip(similars, prices):
            message += f"Potentially related product:\n{similar}\nPrice is ${price:.2f}\n\n"
        return message

    def messages_for(self, description: str, similars: List[str], prices: List[float]):
        system_message = "You estimate prices of items. Reply only with the price, no explanation"
        user_prompt = self.make_context(similars, prices)
        user_prompt += "And now the question for you:\n\n"
        user_prompt += "How much does this cost?\n\n" + description
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": "Price is $"}
        ]

    def find_similars(self, description: str):
        vector = self.model.encode([description])
        results = self.collection.query(query_embeddings=vector.astype(float).tolist(), n_results=5)
        documents = results['documents'][0][:]
        prices = [m['price'] for m in results['metadatas'][0][:]]
        return documents, prices

    def get_price(self, s) -> float:
        s = s.replace('$','').replace(',','')
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else 0.0

    def price(self, description: str) -> float:
        documents, prices = self.find_similars(description)
        response = self.openai.chat.completions.create(
            model=self.MODEL, 
            messages=self.messages_for(description, documents, prices),
            seed=42,
            max_tokens=5
        )
        reply = response.choices[0].message.content
        return self.get_price(reply)
        