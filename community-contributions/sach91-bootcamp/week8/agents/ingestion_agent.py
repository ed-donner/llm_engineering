"""
Ingestion Agent - Processes and stores documents in the vector database
"""
import logging
from typing import Dict, List
import uuid
from datetime import datetime

from agents.base_agent import BaseAgent
from models.document import Document, DocumentChunk
from utils.document_parser import DocumentParser
from utils.embeddings import EmbeddingModel
import chromadb

logger = logging.getLogger(__name__)

class IngestionAgent(BaseAgent):
    """Agent responsible for ingesting and storing documents"""
    
    def __init__(self, collection: chromadb.Collection, 
                 embedding_model: EmbeddingModel,
                 llm_client=None, model: str = "llama3.2"):
        """
        Initialize ingestion agent
        
        Args:
            collection: ChromaDB collection for storage
            embedding_model: Model for generating embeddings
            llm_client: Optional shared LLM client
            model: Ollama model name
        """
        super().__init__(name="IngestionAgent", llm_client=llm_client, model=model)
        
        self.collection = collection
        self.embedding_model = embedding_model
        self.parser = DocumentParser(chunk_size=1000, chunk_overlap=200)
        
        logger.info(f"{self.name} ready with ChromaDB collection")
    
    def process(self, file_path: str) -> Document:
        """
        Process and ingest a document
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Document object with metadata
        """
        logger.info(f"{self.name} processing: {file_path}")
        
        # Parse the document
        parsed = self.parser.parse_file(file_path)
        
        # Generate document ID
        doc_id = str(uuid.uuid4())
        
        # Create document chunks
        chunks = []
        chunk_texts = []
        chunk_ids = []
        chunk_metadatas = []
        
        for i, chunk_text in enumerate(parsed['chunks']):
            chunk_id = f"{doc_id}_chunk_{i}"
            
            chunk = DocumentChunk(
                id=chunk_id,
                document_id=doc_id,
                content=chunk_text,
                chunk_index=i,
                metadata={
                    'filename': parsed['filename'],
                    'extension': parsed['extension'],
                    'total_chunks': len(parsed['chunks'])
                }
            )
            
            chunks.append(chunk)
            chunk_texts.append(chunk_text)
            chunk_ids.append(chunk_id)
            chunk_metadatas.append({
                'document_id': doc_id,
                'filename': parsed['filename'],
                'chunk_index': i,
                'extension': parsed['extension']
            })
        
        # Generate embeddings
        logger.info(f"{self.name} generating embeddings for {len(chunks)} chunks")
        embeddings = self.embedding_model.embed_documents(chunk_texts)
        
        # Store in ChromaDB
        logger.info(f"{self.name} storing in ChromaDB")
        self.collection.add(
            ids=chunk_ids,
            documents=chunk_texts,
            embeddings=embeddings,
            metadatas=chunk_metadatas
        )
        
        # Create document object
        document = Document(
            id=doc_id,
            filename=parsed['filename'],
            filepath=parsed['filepath'],
            content=parsed['text'],
            chunks=chunks,
            metadata={
                'extension': parsed['extension'],
                'num_chunks': len(chunks),
                'total_chars': parsed['total_chars']
            },
            created_at=datetime.now()
        )
        
        logger.info(f"{self.name} successfully ingested: {document}")
        return document
    
    def get_statistics(self) -> Dict:
        """Get statistics about stored documents"""
        try:
            count = self.collection.count()
            return {
                'total_chunks': count,
                'collection_name': self.collection.name
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {'total_chunks': 0, 'error': str(e)}
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks of a document
        
        Args:
            document_id: ID of document to delete
            
        Returns:
            True if successful
        """
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"{self.name} deleted document {document_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
