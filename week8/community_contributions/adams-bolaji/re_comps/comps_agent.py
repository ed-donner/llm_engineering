"""
CompsAgent - RAG-based real estate price estimator using comparable sales.
Finds similar sold properties in the vector store and uses an LLM to estimate value.
"""
import re
from typing import List, Dict
from openai import OpenAI
from sentence_transformers import SentenceTransformer

# Import base Agent from week8 (path set by run script)
from agents.agent import Agent


class CompsAgent(Agent):
    """
    Estimates property value using RAG over a vector store of comparable sales.
    Similar to FrontierAgent: retrieve similar sold properties, provide context to LLM.
    """

    name = "Comps Agent"
    color = Agent.BLUE
    MODEL = "gpt-4o-mini"

    def __init__(self, collection):
        self.log("Comps Agent is initializing")
        self.client = OpenAI()
        self.collection = collection
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.log("Comps Agent is ready")

    def make_context(self, similars: List[str], prices: List[float]) -> str:
        """Create context from comparable sold properties for the LLM."""
        message = (
            "Here are recent comparable sales (comps) that may help you estimate the property value:\n\n"
        )
        for similar, price in zip(similars, prices):
            message += f"Comparable:\n{similar}\nSold for: ${price:,.0f}\n\n"
        return message

    def messages_for(
        self, description: str, similars: List[str], prices: List[float]
    ) -> List[Dict[str, str]]:
        """Build the message list for the LLM."""
        message = (
            f"Estimate the fair market value of this property based on the comparable sales provided. "
            f"Respond with only the estimated price as a number, no explanation or currency symbol.\n\n"
            f"Property to estimate:\n{description}\n\n"
        )
        message += self.make_context(similars, prices)
        return [{"role": "user", "content": message}]

    def find_comps(self, description: str, n_results: int = 5):
        """Retrieve comparable sold properties from the vector store."""
        self.log("Comps Agent is searching for comparable sales in the vector store")
        vector = self.model.encode([description])
        results = self.collection.query(
            query_embeddings=vector.astype(float).tolist(), n_results=n_results
        )
        documents = results["documents"][0][:]
        prices = [float(m["sale_price"]) for m in results["metadatas"][0][:]]
        self.log(f"Comps Agent found {len(documents)} comparable sales")
        return documents, prices

    def get_price(self, s: str) -> float:
        """Extract a float price from LLM response."""
        s = str(s).replace("$", "").replace(",", "")
        match = re.search(r"[-+]?\d*\.?\d+", s)
        return float(match.group()) if match else 0.0

    def estimate(self, description: str) -> float:
        """
        Estimate the fair market value of a property using RAG.
        """
        documents, prices = self.find_comps(description)
        if not documents:
            self.log("Comps Agent: No comps found, returning 0")
            return 0.0

        self.log(f"Comps Agent is calling {self.MODEL} with {len(documents)} comps")
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=self.messages_for(description, documents, prices),
            seed=42,
        )
        reply = response.choices[0].message.content
        result = self.get_price(reply)
        self.log(f"Comps Agent completed - estimated value ${result:,.0f}")
        return result
