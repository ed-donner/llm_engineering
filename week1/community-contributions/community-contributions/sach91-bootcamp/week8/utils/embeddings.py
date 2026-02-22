"""
Embeddings utility using sentence-transformers
"""
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import logging

logger = logging.getLogger(__name__)

class EmbeddingModel:
    """Wrapper for sentence transformer embeddings"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding model
        
        Args:
            model_name: HuggingFace model name for embeddings
        """
        self.model_name = model_name
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.dimension}")
    
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text(s)
        
        Args:
            texts: Single text or list of texts
            
        Returns:
            Numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query - returns as list for ChromaDB compatibility
        
        Args:
            query: Query text
            
        Returns:
            List of floats representing the embedding
        """
        embedding = self.model.encode([query], show_progress_bar=False)[0]
        return embedding.tolist()
    
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Embed multiple documents - returns as list of lists for ChromaDB
        
        Args:
            documents: List of document texts
            
        Returns:
            List of embeddings (each as list of floats)
        """
        embeddings = self.model.encode(documents, show_progress_bar=False)
        return embeddings.tolist()
    
    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        emb1, emb2 = self.model.encode([text1, text2])
        
        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)
