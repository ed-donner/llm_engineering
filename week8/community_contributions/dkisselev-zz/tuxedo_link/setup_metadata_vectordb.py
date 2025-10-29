"""
Vector database for semantic search of colors and breeds.

This module provides fuzzy matching for user color/breed terms against
valid API values using sentence embeddings.
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


class MetadataVectorDB:
    """
    Vector database for semantic search of metadata (colors, breeds).
    
    Separate from the main cat vector DB, this stores valid API values
    and enables fuzzy matching for user terms.
    """
    
    def __init__(self, persist_directory: str = "metadata_vectorstore"):
        """
        Initialize metadata vector database.
        
        Args:
            persist_directory: Path to persist the database
        """
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Initialize embedding model (same as main vector DB for consistency)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get or create collections
        self.colors_collection = self.client.get_or_create_collection(
            name="colors",
            metadata={"description": "Valid color values from APIs"}
        )
        
        self.breeds_collection = self.client.get_or_create_collection(
            name="breeds",
            metadata={"description": "Valid breed values from APIs"}
        )
        
        logging.info(f"MetadataVectorDB initialized at {persist_directory}")
        logging.info(f"Colors indexed: {self.colors_collection.count()}")
        logging.info(f"Breeds indexed: {self.breeds_collection.count()}")
    
    def index_colors(self, valid_colors: List[str], source: str = "petfinder") -> None:
        """
        Index valid color values for semantic search.
        
        Args:
            valid_colors: List of valid color strings from API
            source: API source (petfinder or rescuegroups)
        """
        if not valid_colors:
            logging.warning(f"No colors provided for indexing from {source}")
            return
        
        # Check if already indexed for this source
        existing = self.colors_collection.get(
            where={"source": source}
        )
        
        if existing and len(existing['ids']) > 0:
            logging.info(f"Colors from {source} already indexed ({len(existing['ids'])} items)")
            return
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(valid_colors, show_progress_bar=False)
        
        # Create IDs
        ids = [f"{source}_color_{i}" for i in range(len(valid_colors))]
        
        # Index in ChromaDB
        self.colors_collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=valid_colors,
            metadatas=[{"color": c, "source": source} for c in valid_colors]
        )
        
        logging.info(f"✓ Indexed {len(valid_colors)} colors from {source}")
    
    def index_breeds(self, valid_breeds: List[str], source: str = "petfinder") -> None:
        """
        Index valid breed values for semantic search.
        
        Args:
            valid_breeds: List of valid breed strings from API
            source: API source (petfinder or rescuegroups)
        """
        if not valid_breeds:
            logging.warning(f"No breeds provided for indexing from {source}")
            return
        
        # Check if already indexed for this source
        existing = self.breeds_collection.get(
            where={"source": source}
        )
        
        if existing and len(existing['ids']) > 0:
            logging.info(f"Breeds from {source} already indexed ({len(existing['ids'])} items)")
            return
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(valid_breeds, show_progress_bar=False)
        
        # Create IDs
        ids = [f"{source}_breed_{i}" for i in range(len(valid_breeds))]
        
        # Index in ChromaDB
        self.breeds_collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=valid_breeds,
            metadatas=[{"breed": b, "source": source} for b in valid_breeds]
        )
        
        logging.info(f"✓ Indexed {len(valid_breeds)} breeds from {source}")
    
    def search_color(
        self, 
        user_term: str, 
        n_results: int = 1,
        source_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Find most similar valid color(s) to user term.
        
        Args:
            user_term: User's color preference (e.g., "tuxedo", "grey")
            n_results: Number of results to return
            source_filter: Optional filter by source (petfinder/rescuegroups)
            
        Returns:
            List of dicts with 'color', 'distance', 'source' keys
        """
        if not user_term or not user_term.strip():
            return []
        
        # Generate embedding for user term
        embedding = self.embedding_model.encode([user_term], show_progress_bar=False)[0]
        
        # Query ChromaDB
        where_filter = {"source": source_filter} if source_filter else None
        
        results = self.colors_collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=min(n_results, self.colors_collection.count()),
            where=where_filter
        )
        
        if not results or not results['ids'] or len(results['ids'][0]) == 0:
            return []
        
        # Format results
        matches = []
        for i in range(len(results['ids'][0])):
            matches.append({
                "color": results['metadatas'][0][i]['color'],
                "distance": results['distances'][0][i],
                "similarity": 1.0 - results['distances'][0][i],  # Convert distance to similarity
                "source": results['metadatas'][0][i]['source']
            })
        
        return matches
    
    def search_breed(
        self, 
        user_term: str, 
        n_results: int = 1,
        source_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Find most similar valid breed(s) to user term.
        
        Args:
            user_term: User's breed preference (e.g., "siamese", "main coon")
            n_results: Number of results to return
            source_filter: Optional filter by source (petfinder/rescuegroups)
            
        Returns:
            List of dicts with 'breed', 'distance', 'source' keys
        """
        if not user_term or not user_term.strip():
            return []
        
        # Generate embedding for user term
        embedding = self.embedding_model.encode([user_term], show_progress_bar=False)[0]
        
        # Query ChromaDB
        where_filter = {"source": source_filter} if source_filter else None
        
        results = self.breeds_collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=min(n_results, self.breeds_collection.count()),
            where=where_filter
        )
        
        if not results or not results['ids'] or len(results['ids'][0]) == 0:
            return []
        
        # Format results
        matches = []
        for i in range(len(results['ids'][0])):
            matches.append({
                "breed": results['metadatas'][0][i]['breed'],
                "distance": results['distances'][0][i],
                "similarity": 1.0 - results['distances'][0][i],
                "source": results['metadatas'][0][i]['source']
            })
        
        return matches
    
    def clear_all(self) -> None:
        """Clear all indexed data (for testing)."""
        try:
            self.client.delete_collection("colors")
            self.client.delete_collection("breeds")
            logging.info("Cleared all metadata collections")
        except Exception as e:
            logging.warning(f"Error clearing collections: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about indexed data."""
        return {
            "colors_count": self.colors_collection.count(),
            "breeds_count": self.breeds_collection.count()
        }

