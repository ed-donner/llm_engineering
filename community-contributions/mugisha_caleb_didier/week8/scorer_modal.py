"""
Modal-deployed relevance scorer using SentenceTransformer embeddings.

Deploy with: uv run modal deploy community-contributions/mugisha_caleb_didier/week8/scorer_modal.py
"""

import modal
from modal import Image

app = modal.App("newshound-scorer")
image = Image.debian_slim().pip_install("sentence-transformers", "numpy")

TOPICS = [
    "artificial intelligence and machine learning breakthroughs",
    "programming languages and software development tools",
    "startup funding and tech industry business news",
    "cybersecurity vulnerabilities and data privacy",
    "open source software releases and developer tools",
    "cloud computing infrastructure and DevOps",
    "web development frameworks and frontend engineering",
]


secrets = [modal.Secret.from_name("huggingface-secret")]


@app.cls(image=image, secrets=secrets, timeout=300)
class Scorer:
    @modal.enter()
    def setup(self):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.topic_vectors = self.model.encode(TOPICS)

    @modal.method()
    def score(self, text: str) -> float:
        import numpy as np

        vec = self.model.encode([text])[0]
        norms = np.linalg.norm(self.topic_vectors, axis=1) * np.linalg.norm(vec)
        sims = np.dot(self.topic_vectors, vec) / norms
        return round(float(sims.max()) * 10, 2)
