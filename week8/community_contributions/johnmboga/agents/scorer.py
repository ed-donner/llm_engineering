"""
agents/scorer.py
Agent 2: Embedding-Based Fit Scorer (HuggingFace — Open Source)
Embeds the user CV and each job description using a local
sentence-transformer model, then returns cosine similarity as the fit score.

Model: sentence-transformers/all-MiniLM-L6-v2
- 22M parameters, runs on CPU comfortably
- 384-dimensional embeddings
- Strong performance on semantic similarity tasks
"""

import hashlib
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np


class Scorer:
    """Scores job fit using sentence-transformers embeddings and cosine similarity."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model: SentenceTransformer | None = None
        self._cv_embedding: np.ndarray | None = None
        self._cv_text_hash: str = ""

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            print(f"[Scorer] Loading embedding model: {self._model_name}")
            self._model = SentenceTransformer(self._model_name)
            print("[Scorer] Model loaded ✅")
        return self._model

    def _embed(self, text: str) -> np.ndarray:
        model = self._get_model()
        return model.encode([text], convert_to_numpy=True)

    def _get_cv_embedding(self, cv_text: str) -> np.ndarray:
        h = hashlib.md5(cv_text.encode()).hexdigest()
        if self._cv_embedding is None or h != self._cv_text_hash:
            print("[Scorer] Embedding CV...")
            self._cv_embedding = self._embed(cv_text)
            self._cv_text_hash = h
            print("[Scorer] CV embedded ✅")
        return self._cv_embedding

    def score_fit(self, cv_text: str, job_description: str) -> float:
        """
        Returns a float [0, 1] representing how well the job description
        matches the candidate's CV. Higher = better fit.
        """
        cv_emb = self._get_cv_embedding(cv_text)
        job_emb = self._embed(job_description)
        similarity = cosine_similarity(cv_emb, job_emb)[0][0]
        return float(np.clip(similarity, 0.0, 1.0))

    def preload_model(self) -> None:
        """Call at startup to avoid first-query delay."""
        self._get_model()
