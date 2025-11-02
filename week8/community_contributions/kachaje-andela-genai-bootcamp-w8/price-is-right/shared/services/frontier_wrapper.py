import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import os
import re
import math
import json
from typing import List, Dict
import ollama
from sentence_transformers import SentenceTransformer
import chromadb
from agents.agent import Agent

class FrontierAgentWrapper(Agent):

    name = "Frontier Agent"
    color = Agent.BLUE

    MODEL = "llama3.2:3b-instruct-q4_0"
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    def __init__(self):
        """
        Set up this instance by connecting to Ollama, to the Chroma Datastore,
        And setting up the vector encoding model
        """
        self.log("Initializing Frontier Agent")
        self.client = ollama.Client(host=self.OLLAMA_HOST)
        self.log("Frontier Agent is set up with Ollama")
        
        # Initialize ChromaDB
        self.collection = chromadb.PersistentClient(path='data/vectorstore').get_or_create_collection('products')
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
        Create the message list to be included in a call to Ollama
        With the system and user prompt
        :param description: a description of the product
        :param similars: similar products to this one
        :param prices: prices of similar products
        :return: the list of messages in the format expected by Ollama
        """
        system_message = "You estimate prices of items. Reply only with the price, no explanation"
        user_prompt = self.make_context(similars, prices)
        user_prompt += "And now the question for you:\n\n"
        user_prompt += "How much does this cost?\n\n" + description
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
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
        Make a call to Ollama to estimate the price of the described product,
        by looking up 5 similar products and including them in the prompt to give context
        :param description: a description of the product
        :return: an estimate of the price
        """
        documents, prices = self.find_similars(description)
        self.log(f"Frontier Agent is about to call {self.MODEL} with context including 5 similar products")
        
        try:
            self.log(f"Connecting to Ollama at {self.OLLAMA_HOST}")
            response = self.client.chat(
                model=self.MODEL, 
                messages=self.messages_for(description, documents, prices)
            )
            reply = response['message']['content']
            self.log(f"Raw response from Ollama: {reply}")
            result = self.get_price(reply)
            self.log(f"Frontier Agent completed - predicting ${result:.2f}")
            return result
        except Exception as e:
            self.log(f"Error calling Ollama: {str(e)}")
            self.log(f"Ollama host: {self.OLLAMA_HOST}")
            self.log(f"Model: {self.MODEL}")
            
            # Fallback: simple keyword-based pricing for testing
            self.log("Using fallback pricing logic")
            fallback_price = self._fallback_pricing(description)
            self.log(f"Fallback price: ${fallback_price:.2f}")
            return fallback_price
    
    def _fallback_pricing(self, description: str) -> float:
        """
        Simple fallback pricing based on keywords for testing
        """
        description_lower = description.lower()
        
        # Basic keyword-based pricing
        if any(word in description_lower for word in ['iphone', 'iphone 15', 'pro max']):
            return 1200.0
        elif any(word in description_lower for word in ['macbook', 'macbook pro', 'm3']):
            return 2000.0
        elif any(word in description_lower for word in ['samsung', 'galaxy', 's24']):
            return 1000.0
        elif any(word in description_lower for word in ['sony', 'headphones', 'wh-1000xm5']):
            return 400.0
        elif any(word in description_lower for word in ['laptop', 'computer']):
            return 800.0
        elif any(word in description_lower for word in ['phone', 'smartphone']):
            return 600.0
        elif any(word in description_lower for word in ['tablet', 'ipad']):
            return 500.0
        else:
            return 100.0  # Default fallback price
