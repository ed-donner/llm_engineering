import re
from typing import List, Dict, Tuple
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from .base_agent import Agent


class RAGPriceAgent(Agent):
    """
    RAG-based Price Estimation Agent.
    Uses vector similarity search to find similar products and
    leverages GPT to estimate price based on context.
    """

    name = "RAG Price Agent"
    color = Agent.BLUE
    MODEL = "gpt-4o-mini"

    def __init__(self, collection, currency: str = "₦"):
        """
        Initialize the RAG agent with a ChromaDB collection.
        
        Args:
            collection: ChromaDB collection containing product embeddings
            currency: Currency symbol (default: Nigerian Naira)
        """
        self.log("Initializing RAG Price Agent")
        self.client = OpenAI()
        self.collection = collection
        self.currency = currency
        self.encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.log("RAG Price Agent ready")

    def find_similar_products(self, description: str, n_results: int = 5) -> Tuple[List[str], List[float]]:
        """
        Find similar products using vector similarity search.
        
        Args:
            description: Product description to search for
            n_results: Number of similar products to retrieve
            
        Returns:
            Tuple of (product descriptions, prices)
        """
        self.log(f"Searching for {n_results} similar products")
        vector = self.encoder.encode([description])
        results = self.collection.query(
            query_embeddings=vector.astype(float).tolist(),
            n_results=n_results
        )
        documents = results["documents"][0][:]
        prices = [m["price"] for m in results["metadatas"][0][:]]
        self.log(f"Found {len(documents)} similar products")
        return documents, prices

    def build_context(self, similar_products: List[str], prices: List[float]) -> str:
        """Build context string from similar products."""
        context = "Here are similar products for price reference:\n\n"
        for product, price in zip(similar_products, prices):
            context += f"Product: {product}\nPrice: {self.currency}{price:,.2f}\n\n"
        return context

    def build_messages(self, description: str, context: str) -> List[Dict[str, str]]:
        """Build the message list for OpenAI API."""
        system_prompt = f"""You are an expert Nigerian market price estimator. 
        Analyze the product description and similar products to estimate a fair market price.
        Consider Nigerian market conditions, import costs, and local pricing trends.
        Respond with ONLY the numeric price in {self.currency}, no explanation."""
        
        user_prompt = f"""Estimate the price for this product:

{description}

{context}

Respond with only the price number."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    def extract_price(self, response: str) -> float:
        """Extract numeric price from response string."""
        cleaned = response.replace(self.currency, "").replace(",", "").replace("₦", "").replace("$", "")
        match = re.search(r"[-+]?\d*\.?\d+", cleaned)
        return float(match.group()) if match else 0.0

    def price(self, description: str) -> float:
        """
        Estimate the price of a product using RAG.
        
        Args:
            description: Product description
            
        Returns:
            Estimated price as float
        """
        similar_products, prices = self.find_similar_products(description)
        context = self.build_context(similar_products, prices)
        messages = self.build_messages(description, context)
        
        self.log(f"Calling {self.MODEL} with RAG context")
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=messages,
            temperature=0.1,
            seed=42
        )
        
        result = self.extract_price(response.choices[0].message.content)
        self.log(f"RAG Agent estimate: {self.currency}{result:,.2f}")
        return result
