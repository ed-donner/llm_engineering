import os
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import chromadb
from agents.base_agent import BaseAgent

TRIAGE_LEVELS = ["Immediate", "Urgent", "Semi-urgent", "Non-urgent"]

SYSTEM_MSG = """You are a senior emergency medicine consultant.
You will be given a patient presentation and relevant clinical guidelines.
Classify the triage urgency as exactly one of: Immediate, Urgent, Semi-urgent, Non-urgent.
Respond with one word only."""


class RAGAgent(BaseAgent):
    """
    Retrieves relevant clinical guidelines from ChromaDB, then asks GPT-4.1-mini
    to classify urgency using retrieved context. Grounds the decision in evidence.
    """

    color = BaseAgent.GREEN

    def __init__(self, vector_db_path: str = "clinical_vector_db"):
        self.log("Loading RAG agent...")
        self.client = OpenAI()
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        chroma = chromadb.PersistentClient(path=vector_db_path)
        self.collection = chroma.get_or_create_collection("clinical_guidelines")
        self.log(f"Vector store loaded: {self.collection.count()} chunks")

    def _retrieve(self, presentation: str, n_results: int = 5) -> str:
        embedding = self.embedder.encode(presentation).tolist()
        results = self.collection.query(query_embeddings=[embedding], n_results=n_results)
        chunks = results["documents"][0] if results["documents"] else []
        return "\n\n".join(chunks)

    def classify(self, presentation: str) -> str:
        self.log(f"Retrieving guidelines for: {presentation[:60]}...")
        context = self._retrieve(presentation)

        prompt = f"""Patient presentation: {presentation}

Relevant clinical guidelines:
{context}

Based on the above, what is the triage level?"""

        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SYSTEM_MSG},
                {"role": "user", "content": prompt},
            ],
            max_tokens=10,
            temperature=0,
        )
        result = response.choices[0].message.content.strip()
        for level in TRIAGE_LEVELS:
            if level.lower() in result.lower():
                self.log(f"Result: {level}")
                return level
        self.log(f"Unknown result: {result}")
        return "Unknown"
