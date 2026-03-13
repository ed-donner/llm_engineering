"""RAG-based fit agent: scores how well an opportunity matches the game-publisher KB (indie-friendly criteria)."""
import re
from typing import List, Tuple

import chromadb
from sentence_transformers import SentenceTransformer

from agents.agent import Agent
from config import PUBLISHER_DB_PATH
from llm_client import get_client, get_model
from publisher_models import PublisherOpportunity

COLLECTION_NAME = "publisher_kb"


class PublisherFitAgent(Agent):
    """Scores 0-100 by retrieving relevant chunks from game_publisher_db and asking LLM for fit."""

    name = "Publisher Fit Agent (RAG)"
    color = Agent.BLUE
    N_RESULTS = 5

    def __init__(self) -> None:
        self.log("Initializing Publisher Fit Agent (RAG)")
        self._client: chromadb.PersistentClient | None = None
        self._collection = None
        self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self._llm = get_client()
        self._model_id = get_model()
        self.log("Publisher Fit Agent is ready")

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        # Build vector store from game-publisher-kb if it doesn't exist (all inside week8)
        if not PUBLISHER_DB_PATH.exists():
            self.log("Vector store not found; building from game-publisher-kb...")
            try:
                from build_vectorstore import build
                build()
            except Exception as e:
                self.log(f"Failed to build vector store: {e}; RAG scores will fall back to 50")
                return None
        self._client = chromadb.PersistentClient(path=str(PUBLISHER_DB_PATH))
        try:
            self._collection = self._client.get_collection(name=COLLECTION_NAME)
        except Exception:
            self.log("Collection not found; rebuilding vector store...")
            try:
                from build_vectorstore import build
                build()
                self._collection = self._client.get_collection(name=COLLECTION_NAME)
            except Exception as e:
                self.log(f"Failed to get collection: {e}")
                return None
        return self._collection

    def _retrieve(self, opportunity: PublisherOpportunity) -> Tuple[List[str], List[dict]]:
        """Return (documents, metadatas) for the opportunity text."""
        coll = self._get_collection()
        if coll is None:
            return [], []
        text = f"{opportunity.name}\n{opportunity.description}"
        if opportunity.eligibility_summary:
            text += f"\n{opportunity.eligibility_summary}"
        vector = self._model.encode([text])
        results = coll.query(
            query_embeddings=vector.astype(float).tolist(),
            n_results=min(self.N_RESULTS, coll.count()),
            include=["documents", "metadatas"],
        )
        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []
        return docs, metas

    @staticmethod
    def _parse_score(reply: str) -> float:
        s = reply.replace("$", "").replace(",", "")
        match = re.search(r"\b(\d{1,3}(?:\.\d+)?)\s*(?:/|out of)?\s*100?", s)
        if match:
            return min(100.0, max(0.0, float(match.group(1))))
        match = re.search(r"\b(\d{1,3}(?:\.\d+)?)\b", s)
        if match:
            return min(100.0, max(0.0, float(match.group(1))))
        return 50.0

    def score(self, opportunity: PublisherOpportunity) -> float:
        """
        Score 0-100 how well this opportunity matches our publisher KB (indie-friendly, genre, scope, platform).
        Uses RAG over game_publisher_db.
        """
        self.log(f"Scoring opportunity: {opportunity.name[:50]}...")
        docs, _ = self._retrieve(opportunity)
        if not docs:
            self.log("No RAG context; using default score 50")
            return 50.0
        context = "\n\n".join(docs[:5])
        user_content = (
            "You have context from an indie game publisher's internal docs (submission guidelines, revenue, platforms, team).\n\n"
            "Score from 0 to 100 how well this opportunity matches those criteria: indie-friendly genres (roguelike, puzzle, narrative, tactics, survival, arcade), small team scope (6-18 months), PC/console platforms, clear submission process.\n\n"
            "Opportunity:\n"
            f"Name: {opportunity.name}\n"
            f"Description: {opportunity.description}\n\n"
            "Relevant publisher context:\n"
            f"{context[:3000]}\n\n"
            "Reply with a single number 0-100 (e.g. 75)."
        )
        try:
            response = self._llm.chat.completions.create(
                model=self._model_id,
                messages=[{"role": "user", "content": user_content}],
            )
            reply = response.choices[0].message.content or ""
            score = self._parse_score(reply)
            self.log(f"Publisher Fit Agent score: {score:.1f}")
            return score
        except Exception as e:
            self.log(f"OpenRouter/LLM error: {e}; returning 50")
            return 50.0
