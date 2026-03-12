"""
Research Agent - RAG over filings with LLM synthesis.
Finds similar filing chunks and produces a research summary.
"""

from typing import List, Tuple
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from agents.agent import Agent


class ResearchAgent(Agent):
    name = "Research Agent"
    color = Agent.BLUE
    MODEL = "gpt-4o-mini"

    def __init__(self, collection):
        self.log("Initializing Research Agent")
        self.client = OpenAI(base_url= self.openrouter_base_url)
        self.collection = collection
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.log("Research Agent is ready")

    def find_similars(self, ticker: str, query: str, n_results: int = 5) -> Tuple[List[str], List[dict]]:
        """Query Chroma for similar filing chunks, optionally filtered by ticker."""
        self.log(f"RAG search for ticker={ticker}, query='{query[:50]}...'")
        vector = self.model.encode([query])
        where_filter = None
        if ticker:
            where_filter = {"ticker": ticker}
        try:
            results = self.collection.query(
                query_embeddings=vector.astype(float).tolist(),
                n_results=min(n_results, 10),
                where=where_filter if where_filter else None,
            )
        except Exception:
            results = self.collection.query(
                query_embeddings=vector.astype(float).tolist(),
                n_results=min(n_results, 10),
            )
        documents = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        self.log(f"Found {len(documents)} similar filing chunks")
        return documents, metadatas

    def research(self, ticker: str, focus: str = "investment outlook") -> str:
        """
        Produce a research summary for the ticker using RAG context.
        focus: optional focus area (e.g., "risk factors", "revenue growth")
        """
        self.log(f"Researching {ticker} with focus: {focus}")
        query = f"{ticker} {focus}"
        documents, metadatas = self.find_similars(ticker, query)
        if not documents:
            self.log("No filing context found - using generic placeholder")
            return f"No filing data found for {ticker}. Consider building the vector store with helpers/build_filings_vectorstore.py"

        context = "\n\n".join(documents[:5])
        prompt = f"""Based on the following excerpts from SEC filings and company documents for {ticker}, 
write a 2-3 paragraph research summary covering key business highlights, financial position, and {focus}.

Excerpts:
{context}

Provide a balanced, factual research summary suitable for investment analysis."""

        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            seed=42,
        )
        summary = response.choices[0].message.content
        self.log("Research Agent completed summary")
        return summary
