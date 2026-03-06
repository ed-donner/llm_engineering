import os
import re
import sys
from typing import List, Dict
from openai import OpenAI
from sentence_transformers import SentenceTransformer

w8d5_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if w8d5_path not in sys.path:
    sys.path.insert(0, w8d5_path)

from agents.agent import Agent


class TravelEstimatorAgent(Agent):

    name = "Travel Estimator"
    color = Agent.BLUE

    MODEL = "gpt-4o-mini"
    
    def __init__(self, collection):
        self.log("Travel Estimator initializing")
        self.client = OpenAI()
        self.MODEL = "gpt-4o-mini"
        self.log("Travel Estimator using OpenAI")
        self.collection = collection
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.log("Travel Estimator ready")

    def make_context(self, similars: List[str], prices: List[float]) -> str:
        message = "Here are similar travel deals for context:\n\n"
        for similar, price in zip(similars, prices):
            message += f"Similar deal:\n{similar}\nPrice: ${price:.2f}\n\n"
        return message

    def messages_for(self, description: str, similars: List[str], prices: List[float]) -> List[Dict[str, str]]:
        system_message = "You estimate fair market prices for travel deals. Reply only with the price estimate, no explanation"
        user_prompt = self.make_context(similars, prices)
        user_prompt += "Now estimate the fair market price for:\n\n"
        user_prompt += description
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": "Fair price estimate: $"}
        ]

    def find_similars(self, description: str):
        self.log("Travel Estimator searching for similar deals")
        vector = self.model.encode([description])
        results = self.collection.query(query_embeddings=vector.astype(float).tolist(), n_results=5)
        documents = results['documents'][0][:]
        prices = [m['price'] for m in results['metadatas'][0][:]]
        self.log("Travel Estimator found similar deals")
        return documents, prices

    def get_price(self, s) -> float:
        s = s.replace('$','').replace(',','')
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else 0.0

    def estimate(self, description: str) -> float:
        documents, prices = self.find_similars(description)
        self.log(f"Travel Estimator calling {self.MODEL}")
        response = self.client.chat.completions.create(
            model=self.MODEL, 
            messages=self.messages_for(description, documents, prices),
            seed=42,
            max_tokens=10
        )
        reply = response.choices[0].message.content
        result = self.get_price(reply)
        self.log(f"Travel Estimator complete - ${result:.2f}")
        return result

