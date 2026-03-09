"""
Text embedding utilities using sentence-transformers
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Optional
from tqdm import tqdm
import os


class EmbeddingGenerator:
    """
    Generate and manage text embeddings for product descriptions
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', cache_dir: Optional[str] = None):
        """
        Initialize embedding generator
        
        Args:
            model_name: Name of sentence-transformer model
            cache_dir: Directory to cache embeddings
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        print(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        print(f"Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as numpy array
        """
        if not text:
            # Return zero vector for empty text
            dim = self.model.get_sentence_embedding_dimension()
            return np.zeros(dim)
        
        return self.model.encode(text, convert_to_numpy=True)
    
    def embed_batch(self, texts: List[str], batch_size: int = 32, show_progress: bool = True) -> np.ndarray:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            
        Returns:
            Array of embeddings (n_texts, embedding_dim)
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        return embeddings
    
    def embed_items(self, items: List, use_summary: bool = True, show_progress: bool = True) -> np.ndarray:
        """
        Generate embeddings for a list of Item objects
        
        Args:
            items: List of Item objects
            use_summary: Use summary field (True) or full field (False)
            show_progress: Show progress bar
            
        Returns:
            Array of embeddings
        """
        texts = []
        for item in items:
            if use_summary and item.summary:
                texts.append(item.summary)
            elif item.full:
                texts.append(item.full)
            else:
                texts.append(item.title)
        
        return self.embed_batch(texts, show_progress=show_progress)
    
    def save_embeddings(self, embeddings: np.ndarray, filepath: str):
        """Save embeddings to disk"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        np.save(filepath, embeddings)
        print(f"Embeddings saved to {filepath}")
    
    def load_embeddings(self, filepath: str) -> np.ndarray:
        """Load embeddings from disk"""
        embeddings = np.load(filepath)
        print(f"Embeddings loaded from {filepath}. Shape: {embeddings.shape}")
        return embeddings
    
    def compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            emb1: First embedding
            emb2: Second embedding
            
        Returns:
            Cosine similarity score (0-1)
        """
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def find_most_similar(self, query_embedding: np.ndarray, 
                         embeddings: np.ndarray, 
                         top_k: int = 5) -> List[tuple]:
        """
        Find most similar embeddings to query
        
        Args:
            query_embedding: Query embedding vector
            embeddings: Array of embeddings to search
            top_k: Number of top results to return
            
        Returns:
            List of (index, similarity_score) tuples
        """
        # Compute similarities
        similarities = []
        for idx, emb in enumerate(embeddings):
            sim = self.compute_similarity(query_embedding, emb)
            similarities.append((idx, sim))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]


def batch_embed_items(items: List, 
                     model_name: str = 'all-MiniLM-L6-v2',
                     cache_path: Optional[str] = None) -> np.ndarray:
    """
    Convenience function to embed items with optional caching
    
    Args:
        items: List of Item objects
        model_name: Sentence transformer model name
        cache_path: Path to cache embeddings
        
    Returns:
        Array of embeddings
    """
    # Check if cached embeddings exist
    if cache_path and os.path.exists(cache_path):
        print(f"Loading cached embeddings from {cache_path}")
        return np.load(cache_path)
    
    # Generate embeddings
    generator = EmbeddingGenerator(model_name)
    embeddings = generator.embed_items(items, use_summary=True, show_progress=True)
    
    # Cache if path provided
    if cache_path:
        generator.save_embeddings(embeddings, cache_path)
    
    return embeddings
