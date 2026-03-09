"""
Retrieval-Augmented Generation (RAG) system for price prediction
"""

import numpy as np
import faiss
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SimilarProduct:
    """Container for similar product information"""
    index: int
    similarity: float
    price: float
    title: str
    category: str


class RAGSystem:
    """
    RAG system for finding similar products and using their prices as context
    """
    
    def __init__(self, embeddings: np.ndarray, items: List, index_type: str = 'flat'):
        """
        Initialize RAG system
        
        Args:
            embeddings: Product embeddings (n_items, embedding_dim)
            items: List of Item objects
            index_type: Type of FAISS index ('flat' or 'ivf')
        """
        self.embeddings = embeddings
        self.items = items
        self.index = None
        self.index_type = index_type
        self._build_index()
    
    def _build_index(self):
        """Build FAISS index for fast similarity search"""
        dimension = self.embeddings.shape[1]
        n_items = self.embeddings.shape[0]
        
        print(f"Building FAISS index with {n_items} items, dimension {dimension}")
        
        if self.index_type == 'flat':
            # Exact search (slower but accurate)
            self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
        elif self.index_type == 'ivf':
            # Approximate search (faster)
            nlist = min(100, n_items // 10)  # Number of clusters
            quantizer = faiss.IndexFlatIP(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            self.index.train(self.embeddings)
        else:
            raise ValueError(f"Unknown index type: {self.index_type}")
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.embeddings)
        
        # Add embeddings to index
        self.index.add(self.embeddings)
        
        print(f"Index built successfully. Total items: {self.index.ntotal}")
    
    def search(self, query_embedding: np.ndarray, k: int = 10, 
               exclude_self: bool = True) -> List[SimilarProduct]:
        """
        Search for similar products
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            exclude_self: Exclude the query item itself from results
            
        Returns:
            List of SimilarProduct objects
        """
        # Normalize query
        query_norm = query_embedding.reshape(1, -1).copy()
        faiss.normalize_L2(query_norm)
        
        # Search
        search_k = k + 1 if exclude_self else k
        similarities, indices = self.index.search(query_norm, search_k)
        
        # Convert to SimilarProduct objects
        results = []
        for idx, sim in zip(indices[0], similarities[0]):
            if exclude_self and idx == 0:  # Skip if it's the same item
                continue
            
            if idx < len(self.items):
                item = self.items[idx]
                results.append(SimilarProduct(
                    index=int(idx),
                    similarity=float(sim),
                    price=item.price,
                    title=item.title,
                    category=item.category
                ))
        
        return results[:k]
    
    def get_price_statistics(self, similar_products: List[SimilarProduct]) -> dict:
        """
        Compute price statistics from similar products
        
        Args:
            similar_products: List of similar products
            
        Returns:
            Dictionary with price statistics
        """
        if not similar_products:
            return {
                'mean': 0,
                'median': 0,
                'std': 0,
                'min': 0,
                'max': 0,
                'count': 0
            }
        
        prices = [p.price for p in similar_products]
        
        return {
            'mean': np.mean(prices),
            'median': np.median(prices),
            'std': np.std(prices),
            'min': np.min(prices),
            'max': np.max(prices),
            'count': len(prices)
        }
    
    def get_weighted_price(self, similar_products: List[SimilarProduct]) -> float:
        """
        Compute weighted average price based on similarity scores
        
        Args:
            similar_products: List of similar products
            
        Returns:
            Weighted average price
        """
        if not similar_products:
            return 0.0
        
        total_weight = sum(p.similarity for p in similar_products)
        if total_weight == 0:
            return np.mean([p.price for p in similar_products])
        
        weighted_sum = sum(p.price * p.similarity for p in similar_products)
        return weighted_sum / total_weight
    
    def augment_item_with_rag(self, item, item_index: int, k: int = 10):
        """
        Augment an item with RAG features
        
        Args:
            item: Item object to augment
            item_index: Index of item in the dataset
            k: Number of similar products to retrieve
        """
        # Get embedding
        query_embedding = self.embeddings[item_index]
        
        # Search for similar products
        similar = self.search(query_embedding, k=k, exclude_self=True)
        
        # Store similar prices
        item.similar_prices = [p.price for p in similar]
        
        # Compute and store statistics
        stats = self.get_price_statistics(similar)
        item.rag_mean_price = stats['mean']
        item.rag_median_price = stats['median']
        item.rag_std_price = stats['std']
        item.rag_weighted_price = self.get_weighted_price(similar)
        
        return similar
    
    def create_rag_context(self, similar_products: List[SimilarProduct], 
                          max_items: int = 5) -> str:
        """
        Create text context from similar products for LLM prompting
        
        Args:
            similar_products: List of similar products
            max_items: Maximum number of items to include
            
        Returns:
            Formatted context string
        """
        if not similar_products:
            return "No similar products found."
        
        context = "Similar products found:\n"
        for i, prod in enumerate(similar_products[:max_items], 1):
            context += f"{i}. {prod.title} - ${prod.price:.2f} (similarity: {prod.similarity:.2f})\n"
        
        # Add statistics
        stats = self.get_price_statistics(similar_products)
        context += f"\nPrice statistics: Mean=${stats['mean']:.2f}, Median=${stats['median']:.2f}, Range=${stats['min']:.2f}-${stats['max']:.2f}"
        
        return context


def build_rag_system(embeddings: np.ndarray, items: List, 
                    index_type: str = 'flat') -> RAGSystem:
    """
    Convenience function to build RAG system
    
    Args:
        embeddings: Product embeddings
        items: List of Item objects
        index_type: FAISS index type
        
    Returns:
        Initialized RAGSystem
    """
    return RAGSystem(embeddings, items, index_type)
