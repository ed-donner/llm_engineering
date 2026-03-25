from typing import Optional
from .base_agent import Agent
from .rag_agent import RAGPriceAgent
from .llm_agent import LLMPriceAgent


class EnsemblePriceAgent(Agent):
    """
    Ensemble Price Estimation Agent.
    Combines multiple pricing strategies for more accurate estimates:
    - RAG-based similarity pricing
    - LLM world knowledge pricing
    - Weighted averaging with configurable weights
    """

    name = "Ensemble Price Agent"
    color = Agent.YELLOW

    def __init__(
        self,
        collection=None,
        currency: str = "₦",
        market: str = "Nigerian",
        rag_weight: float = 0.6,
        llm_weight: float = 0.4
    ):
        """
        Initialize the Ensemble Agent.
        
        Args:
            collection: ChromaDB collection for RAG (optional)
            currency: Currency symbol
            market: Target market
            rag_weight: Weight for RAG agent (0-1)
            llm_weight: Weight for LLM agent (0-1)
        """
        self.log("Initializing Ensemble Price Agent")
        self.currency = currency
        self.rag_weight = rag_weight
        self.llm_weight = llm_weight
        
        self.rag_agent: Optional[RAGPriceAgent] = None
        if collection is not None:
            self.rag_agent = RAGPriceAgent(collection, currency)
            
        self.llm_agent = LLMPriceAgent(currency, market)
        self.log(f"Ensemble ready (RAG: {rag_weight:.0%}, LLM: {llm_weight:.0%})")

    def price(self, description: str) -> float:
        """
        Estimate price using ensemble of agents.
        
        Args:
            description: Product description
            
        Returns:
            Weighted average price estimate
        """
        self.log("Running ensemble price estimation")
        
        llm_price = self.llm_agent.price(description)
        
        if self.rag_agent is not None:
            rag_price = self.rag_agent.price(description)
            combined = (rag_price * self.rag_weight) + (llm_price * self.llm_weight)
            self.log(f"RAG: {self.currency}{rag_price:,.2f} | LLM: {self.currency}{llm_price:,.2f}")
        else:
            combined = llm_price
            self.log("RAG not available, using LLM only")
        
        self.log(f"Ensemble estimate: {self.currency}{combined:,.2f}")
        return combined

    def price_with_confidence(self, description: str) -> dict:
        """
        Estimate price with confidence metrics.
        
        Returns:
            Dictionary with price, individual estimates, and confidence
        """
        self.log("Running ensemble with confidence analysis")
        
        llm_price = self.llm_agent.price(description)
        
        result = {
            "final_price": llm_price,
            "llm_price": llm_price,
            "rag_price": None,
            "confidence": "medium",
            "currency": self.currency
        }
        
        if self.rag_agent is not None:
            rag_price = self.rag_agent.price(description)
            combined = (rag_price * self.rag_weight) + (llm_price * self.llm_weight)
            
            variance = abs(rag_price - llm_price) / max(rag_price, llm_price, 1)
            
            if variance < 0.15:
                confidence = "high"
            elif variance < 0.35:
                confidence = "medium"
            else:
                confidence = "low"
            
            result.update({
                "final_price": combined,
                "rag_price": rag_price,
                "confidence": confidence,
                "variance": variance
            })
        
        self.log(f"Confidence: {result['confidence']} | Price: {self.currency}{result['final_price']:,.2f}")
        return result
