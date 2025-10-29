"""Setup script for ChromaDB vector database."""

import os
import chromadb
from chromadb.config import Settings
from typing import List
from dotenv import load_dotenv

from models.cats import Cat
from sentence_transformers import SentenceTransformer


class VectorDBManager:
    """Manages ChromaDB for cat adoption semantic search."""
    
    COLLECTION_NAME = "cats"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    def __init__(self, persist_directory: str = "cat_vectorstore"):
        """
        Initialize the vector database manager.
        
        Args:
            persist_directory: Directory for ChromaDB persistence
        """
        self.persist_directory = persist_directory
        
        # Create directory if it doesn't exist
        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        print(f"Loading embedding model: {self.EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(self.EMBEDDING_MODEL)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={'description': 'Cat adoption listings with semantic search'}
        )
        
        print(f"Vector database initialized at {persist_directory}")
        print(f"Collection '{self.COLLECTION_NAME}' contains {self.collection.count()} documents")
    
    def create_document_text(self, cat: Cat) -> str:
        """
        Create searchable document text from cat attributes.
        
        Combines description with key attributes for semantic search.
        
        Args:
            cat: Cat object
            
        Returns:
            Document text for embedding
        """
        parts = []
        
        # Add description
        if cat.description:
            parts.append(cat.description)
        
        # Add breed info
        parts.append(f"Breed: {cat.breed}")
        if cat.breeds_secondary:
            parts.append(f"Mixed with: {', '.join(cat.breeds_secondary)}")
        
        # Add personality hints from attributes
        traits = []
        if cat.good_with_children:
            traits.append("good with children")
        if cat.good_with_dogs:
            traits.append("good with dogs")
        if cat.good_with_cats:
            traits.append("good with other cats")
        if cat.house_trained:
            traits.append("house trained")
        if cat.special_needs:
            traits.append("has special needs")
        
        if traits:
            parts.append(f"Personality: {', '.join(traits)}")
        
        # Add color info
        if cat.colors:
            parts.append(f"Colors: {', '.join(cat.colors)}")
        
        return " | ".join(parts)
    
    def create_metadata(self, cat: Cat) -> dict:
        """
        Create metadata dictionary for ChromaDB.
        
        Args:
            cat: Cat object
            
        Returns:
            Metadata dictionary
        """
        return {
            'id': cat.id,
            'name': cat.name,
            'age': cat.age,
            'size': cat.size,
            'gender': cat.gender,
            'breed': cat.breed,
            'city': cat.city or '',
            'state': cat.state or '',
            'zip_code': cat.zip_code or '',
            'latitude': str(cat.latitude) if cat.latitude is not None else '',
            'longitude': str(cat.longitude) if cat.longitude is not None else '',
            'organization': cat.organization_name,
            'source': cat.source,
            'good_with_children': str(cat.good_with_children) if cat.good_with_children is not None else 'unknown',
            'good_with_dogs': str(cat.good_with_dogs) if cat.good_with_dogs is not None else 'unknown',
            'good_with_cats': str(cat.good_with_cats) if cat.good_with_cats is not None else 'unknown',
            'special_needs': str(cat.special_needs),
            'url': cat.url,
            'primary_photo': cat.primary_photo or '',
        }
    
    def add_cat(self, cat: Cat) -> None:
        """
        Add a single cat to the vector database.
        
        Args:
            cat: Cat object to add
        """
        document = self.create_document_text(cat)
        metadata = self.create_metadata(cat)
        
        # Generate embedding
        embedding = self.embedding_model.encode([document])[0].tolist()
        
        # Add to collection
        self.collection.add(
            ids=[cat.id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata]
        )
    
    def add_cats_batch(self, cats: List[Cat], batch_size: int = 100) -> None:
        """
        Add multiple cats to the vector database in batches.
        
        Args:
            cats: List of Cat objects to add
            batch_size: Number of cats to process in each batch
        """
        print(f"Adding {len(cats)} cats to vector database...")
        
        for i in range(0, len(cats), batch_size):
            batch = cats[i:i+batch_size]
            
            # Prepare data
            ids = [cat.id for cat in batch]
            documents = [self.create_document_text(cat) for cat in batch]
            metadatas = [self.create_metadata(cat) for cat in batch]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(documents).tolist()
            
            # Add to collection
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            print(f"Processed batch {i//batch_size + 1}/{(len(cats)-1)//batch_size + 1}")
        
        print(f"Successfully added {len(cats)} cats")
    
    def update_cat(self, cat: Cat) -> None:
        """
        Update an existing cat in the vector database.
        
        Args:
            cat: Updated Cat object
        """
        self.add_cat(cat)
    
    def delete_cat(self, cat_id: str) -> None:
        """
        Delete a cat from the vector database.
        
        Args:
            cat_id: Cat ID to delete
        """
        self.collection.delete(ids=[cat_id])
    
    def search(self, query: str, n_results: int = 50, where: dict = None) -> dict:
        """
        Search for cats using semantic similarity.
        
        Args:
            query: Search query (personality description)
            n_results: Number of results to return
            where: Optional metadata filters
            
        Returns:
            Search results dictionary
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # Search collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=['documents', 'metadatas', 'distances']
        )
        
        return results
    
    def clear_collection(self) -> None:
        """Delete all documents from the collection."""
        print(f"Clearing collection '{self.COLLECTION_NAME}'...")
        self.client.delete_collection(self.COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=self.COLLECTION_NAME,
            metadata={'description': 'Cat adoption listings with semantic search'}
        )
        print("Collection cleared")
    
    def get_stats(self) -> dict:
        """
        Get statistics about the vector database.
        
        Returns:
            Dictionary with stats
        """
        count = self.collection.count()
        return {
            'total_documents': count,
            'collection_name': self.COLLECTION_NAME,
            'persist_directory': self.persist_directory
        }


def initialize_vectordb(persist_directory: str = "cat_vectorstore") -> VectorDBManager:
    """
    Initialize the vector database.
    
    Args:
        persist_directory: Directory for persistence
        
    Returns:
        VectorDBManager instance
    """
    load_dotenv()
    
    # Get directory from environment or use default
    persist_dir = os.getenv('VECTORDB_PATH', persist_directory)
    
    manager = VectorDBManager(persist_dir)
    
    print("\nVector Database Initialized Successfully!")
    print(f"Location: {manager.persist_directory}")
    print(f"Collection: {manager.COLLECTION_NAME}")
    print(f"Documents: {manager.collection.count()}")
    
    return manager


if __name__ == "__main__":
    # Initialize database
    manager = initialize_vectordb()
    
    # Print stats
    stats = manager.get_stats()
    print("\nDatabase Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

