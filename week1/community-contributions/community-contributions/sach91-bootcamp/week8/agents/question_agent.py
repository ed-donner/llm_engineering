"""
Question Agent - Answers questions using RAG (Retrieval Augmented Generation)
"""
import logging
from typing import List, Dict
from agents.base_agent import BaseAgent
from models.document import SearchResult, DocumentChunk
from utils.embeddings import EmbeddingModel
import chromadb

logger = logging.getLogger(__name__)

class QuestionAgent(BaseAgent):
    """Agent that answers questions using retrieved context"""
    
    def __init__(self, collection: chromadb.Collection,
                 embedding_model: EmbeddingModel,
                 llm_client=None, model: str = "llama3.2"):
        """
        Initialize question agent
        
        Args:
            collection: ChromaDB collection with documents
            embedding_model: Model for query embeddings
            llm_client: Optional shared LLM client
            model: Ollama model name
        """
        super().__init__(name="QuestionAgent", llm_client=llm_client, model=model)
        
        self.collection = collection
        self.embedding_model = embedding_model
        self.top_k = 5  # Number of chunks to retrieve
        
        logger.info(f"{self.name} initialized")
    
    def retrieve(self, query: str, top_k: int = None) -> List[SearchResult]:
        """
        Retrieve relevant document chunks for a query
        
        Args:
            query: Search query
            top_k: Number of results to return (uses self.top_k if None)
            
        Returns:
            List of SearchResult objects
        """
        if top_k is None:
            top_k = self.top_k
        
        logger.info(f"{self.name} retrieving top {top_k} chunks for query")
        
        # Generate query embedding
        query_embedding = self.embedding_model.embed_query(query)
        
        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Convert to SearchResult objects
        search_results = []
        
        if results['ids'] and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                chunk = DocumentChunk(
                    id=results['ids'][0][i],
                    document_id=results['metadatas'][0][i].get('document_id', ''),
                    content=results['documents'][0][i],
                    chunk_index=results['metadatas'][0][i].get('chunk_index', 0),
                    metadata=results['metadatas'][0][i]
                )
                
                result = SearchResult(
                    chunk=chunk,
                    score=1.0 - results['distances'][0][i],  # Convert distance to similarity
                    document_id=results['metadatas'][0][i].get('document_id', ''),
                    document_name=results['metadatas'][0][i].get('filename', 'Unknown')
                )
                
                search_results.append(result)
        
        logger.info(f"{self.name} retrieved {len(search_results)} results")
        return search_results
    
    def process(self, question: str, top_k: int = None) -> Dict[str, any]:
        """
        Answer a question using RAG
        
        Args:
            question: User's question
            top_k: Number of chunks to retrieve
            
        Returns:
            Dictionary with answer and sources
        """
        logger.info(f"{self.name} processing question: {question[:100]}...")
        
        # Retrieve relevant chunks
        search_results = self.retrieve(question, top_k)
        
        if not search_results:
            return {
                'answer': "I don't have any relevant information in my knowledge base to answer this question.",
                'sources': [],
                'context_used': ""
            }
        
        # Build context from retrieved chunks
        context_parts = []
        sources = []
        
        for i, result in enumerate(search_results, 1):
            context_parts.append(f"[Source {i}] {result.chunk.content}")
            sources.append({
                'document': result.document_name,
                'score': result.score,
                'preview': result.chunk.content[:150] + "..."
            })
        
        context = "\n\n".join(context_parts)
        
        # Create prompt for LLM
        system_prompt = """You are a helpful research assistant. Answer questions based on the provided context.
Be accurate and cite sources when possible. If the context doesn't contain enough information to answer fully, say so.
Keep your answer concise and relevant."""
        
        user_prompt = f"""Context from my knowledge base:

{context}

Question: {question}

Answer based on the context above. If you reference specific information, mention which source(s) you're using."""
        
        # Generate answer
        answer = self.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.3,  # Lower temperature for more factual responses
            max_tokens=1024
        )
        
        logger.info(f"{self.name} generated answer ({len(answer)} chars)")
        
        return {
            'answer': answer,
            'sources': sources,
            'context_used': context,
            'num_sources': len(sources)
        }
    
    def set_top_k(self, k: int):
        """Set the number of chunks to retrieve"""
        self.top_k = k
        logger.info(f"{self.name} top_k set to {k}")
