# imports

import os
import re
import math
import json
from typing import List, Dict
from openai import OpenAI
try:
    from openai import APIStatusError  
    APIStatusError = Exception  
import statistics
from sentence_transformers import SentenceTransformer
from datasets import load_dataset
import chromadb
from items import Item
from testing import Tester
from agents.agent import Agent


class FrontierAgent(Agent):

    name = "Frontier Agent"
    color = Agent.BLUE

    MODEL = "gpt-4o-mini"
    
    def __init__(self, collection):
        """
        Set up this instance by connecting to OpenAI or DeepSeek, to the Chroma Datastore,
        And setting up the vector encoding model
        """
        self.log("Initializing Frontier Agent")
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_api_key:
            self.client = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")
            self.MODEL = "deepseek-chat"
            self.log("Frontier Agent is set up with DeepSeek")
        else:
            self.client = OpenAI()
            self.MODEL = "gpt-4o-mini"
            self.log("Frontier Agent is setting up with OpenAI")
        self.collection = collection
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.log("Frontier Agent is ready")

    def make_context(self, similars: List[str], prices: List[float]) -> str:
        """
        Create context that can be inserted into the prompt
        :param similars: similar products to the one being estimated
        :param prices: prices of the similar products
        :return: text to insert in the prompt that provides context
        """
        message = "To provide some context, here are some other items that might be similar to the item you need to estimate.\n\n"
        for similar, price in zip(similars, prices):
            message += f"Potentially related product:\n{similar}\nPrice is ${price:.2f}\n\n"
        return message

    def messages_for(self, description: str, similars: List[str], prices: List[float]) -> List[Dict[str, str]]:
        """
        Create the message list to be included in a call to OpenAI
        With the system and user prompt
        :param description: a description of the product
        :param similars: similar products to this one
        :param prices: prices of similar products
        :return: the list of messages in the format expected by OpenAI
        """
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
        """
        Return a list of items similar to the given one by looking in the Chroma datastore
        """
        self.log("Frontier Agent is performing a RAG search of the Chroma datastore to find 5 similar products")
        vector = self.model.encode([description])
        results = self.collection.query(query_embeddings=vector.astype(float).tolist(), n_results=5)
        documents = results['documents'][0][:]
        prices = [m['price'] for m in results['metadatas'][0][:]]
        self.log("Frontier Agent has found similar products")
        return documents, prices

    def get_price(self, s) -> float:
        """
        A utility that plucks a floating point number out of a string
        """
        s = s.replace('$','').replace(',','')
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else 0.0

    def price(self, description: str) -> float:
        """
        Make a call to OpenAI or DeepSeek to estimate the price of the described product,
        by looking up 5 similar products and including them in the prompt to give context
        :param description: a description of the product
        :return: an estimate of the price
        """
        documents, prices = self.find_similars(description)

        # If external calls are disabled, or similar pricing is empty, use heuristic
        allow_external = os.getenv("FRONTIER_ALLOW_EXTERNAL", "true").lower() in {"1", "true", "yes"}

        def heuristic_price() -> float:
            if prices:
                # Robust central tendency fallback
                try:
                    return float(statistics.median(prices))
                except Exception:
                    return float(sum(prices) / max(len(prices), 1))
            # As a last resort, return 0.0
            return 0.0

        if not allow_external:
            self.log("External LLM calls disabled via FRONTIER_ALLOW_EXTERNAL; using heuristic fallback")
            result = heuristic_price()
            self.log(f"Frontier Agent (fallback) - predicting ${result:.2f}")
            return result

        self.log(f"Frontier Agent is about to call {self.MODEL} with context including 5 similar products")
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=self.messages_for(description, documents, prices),
                seed=42,
                max_tokens=5,
            )
            reply = response.choices[0].message.content
            result = self.get_price(reply)
            self.log(f"Frontier Agent completed - predicting ${result:.2f}")
            return result
        except APIStatusError as e:  # Insufficient balance or other HTTP errors
            msg = getattr(e, "message", str(e))
            self.log(f"Frontier Agent API error: {msg}. Falling back to heuristic price.")
            result = heuristic_price()
            self.log(f"Frontier Agent (fallback) - predicting ${result:.2f}")
            return result
        except Exception as e:
            self.log(f"Frontier Agent unexpected error: {e}. Falling back to heuristic price.")
            result = heuristic_price()
            self.log(f"Frontier Agent (fallback) - predicting ${result:.2f}")
            return result


