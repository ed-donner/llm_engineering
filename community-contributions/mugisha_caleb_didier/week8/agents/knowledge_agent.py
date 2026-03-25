from typing import List
from sentence_transformers import SentenceTransformer
from agents.agent import Agent


class KnowledgeAgent(Agent):

    name = "Knowledge Agent"
    color = Agent.BLUE

    def __init__(self, collection):
        self.log("Initializing with ChromaDB")
        self.collection = collection
        self.encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.log("Ready")

    def add_article(self, title: str, summary: str, url: str):
        text = f"{title}. {summary}"
        vector = self.encoder.encode([text]).astype(float).tolist()
        doc_id = f"art_{abs(hash(url)) % 10**9}"
        try:
            self.collection.add(
                ids=[doc_id],
                documents=[text],
                embeddings=vector,
                metadatas=[{"url": url, "title": title[:200]}],
            )
            self.log(f"Stored in knowledge base: {title[:50]}...")
        except Exception:
            pass

    def find_similar(self, text: str, n: int = 3) -> List[str]:
        try:
            count = self.collection.count()
        except Exception:
            count = 0
        if count == 0:
            self.log("Knowledge base empty - no context yet")
            return []
        n = min(n, count)
        vector = self.encoder.encode([text]).astype(float).tolist()
        results = self.collection.query(query_embeddings=vector, n_results=n)
        docs = results["documents"][0] if results["documents"] else []
        self.log(f"RAG search returned {len(docs)} similar past articles")
        return docs

    def size(self) -> int:
        try:
            return self.collection.count()
        except Exception:
            return 0
