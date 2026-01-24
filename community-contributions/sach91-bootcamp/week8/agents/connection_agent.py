"""
Connection Agent - Finds relationships and connections between documents
"""
import logging
from typing import List, Dict, Tuple
from agents.base_agent import BaseAgent
from models.knowledge_graph import KnowledgeNode, KnowledgeEdge, KnowledgeGraph
from utils.embeddings import EmbeddingModel
import chromadb
import numpy as np

logger = logging.getLogger(__name__)

class ConnectionAgent(BaseAgent):
    """Agent that discovers connections between documents and concepts"""
    
    def __init__(self, collection: chromadb.Collection,
                 embedding_model: EmbeddingModel,
                 llm_client=None, model: str = "llama3.2"):
        """
        Initialize connection agent
        
        Args:
            collection: ChromaDB collection with documents
            embedding_model: Model for computing similarities
            llm_client: Optional shared LLM client
            model: Ollama model name
        """
        super().__init__(name="ConnectionAgent", llm_client=llm_client, model=model)
        
        self.collection = collection
        self.embedding_model = embedding_model
        
        logger.info(f"{self.name} initialized")
    
    def process(self, document_id: str = None, query: str = None, 
                top_k: int = 5) -> Dict:
        """
        Find documents related to a document or query
        
        Args:
            document_id: ID of reference document
            query: Search query (used if document_id not provided)
            top_k: Number of related documents to find
            
        Returns:
            Dictionary with related documents and connections
        """
        if document_id:
            logger.info(f"{self.name} finding connections for document: {document_id}")
            return self._find_related_to_document(document_id, top_k)
        elif query:
            logger.info(f"{self.name} finding connections for query: {query[:100]}")
            return self._find_related_to_query(query, top_k)
        else:
            return {'related': [], 'error': 'No document_id or query provided'}
    
    def _find_related_to_document(self, document_id: str, top_k: int) -> Dict:
        """Find documents related to a specific document"""
        try:
            # Get chunks from the document
            results = self.collection.get(
                where={"document_id": document_id},
                include=['embeddings', 'documents', 'metadatas']
            )
            
            if not results['ids']:
                return {'related': [], 'error': 'Document not found'}
            
            # Use the first chunk's embedding as representative
            query_embedding = results['embeddings'][0]
            document_name = results['metadatas'][0].get('filename', 'Unknown')
            
            # Search for similar chunks from OTHER documents
            search_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 3,  # Get more to filter out same document
                include=['documents', 'metadatas', 'distances']
            )
            
            # Filter out chunks from the same document
            related = []
            seen_docs = set([document_id])
            
            if search_results['ids']:
                for i in range(len(search_results['ids'][0])):
                    related_doc_id = search_results['metadatas'][0][i].get('document_id')
                    
                    if related_doc_id not in seen_docs:
                        seen_docs.add(related_doc_id)
                        
                        similarity = 1.0 - search_results['distances'][0][i]
                        
                        related.append({
                            'document_id': related_doc_id,
                            'document_name': search_results['metadatas'][0][i].get('filename', 'Unknown'),
                            'similarity': float(similarity),
                            'preview': search_results['documents'][0][i][:150] + "..."
                        })
                        
                        if len(related) >= top_k:
                            break
            
            return {
                'source_document': document_name,
                'source_id': document_id,
                'related': related,
                'num_related': len(related)
            }
            
        except Exception as e:
            logger.error(f"Error finding related documents: {e}")
            return {'related': [], 'error': str(e)}
    
    def _find_related_to_query(self, query: str, top_k: int) -> Dict:
        """Find documents related to a query"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.embed_query(query)
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 2,  # Get more to deduplicate by document
                include=['documents', 'metadatas', 'distances']
            )
            
            # Deduplicate by document
            related = []
            seen_docs = set()
            
            if results['ids']:
                for i in range(len(results['ids'][0])):
                    doc_id = results['metadatas'][0][i].get('document_id')
                    
                    if doc_id not in seen_docs:
                        seen_docs.add(doc_id)
                        
                        similarity = 1.0 - results['distances'][0][i]
                        
                        related.append({
                            'document_id': doc_id,
                            'document_name': results['metadatas'][0][i].get('filename', 'Unknown'),
                            'similarity': float(similarity),
                            'preview': results['documents'][0][i][:150] + "..."
                        })
                        
                        if len(related) >= top_k:
                            break
            
            return {
                'query': query,
                'related': related,
                'num_related': len(related)
            }
            
        except Exception as e:
            logger.error(f"Error finding related documents: {e}")
            return {'related': [], 'error': str(e)}
    
    def build_knowledge_graph(self, similarity_threshold: float = 0.7) -> KnowledgeGraph:
        """
        Build a knowledge graph showing document relationships
        
        Args:
            similarity_threshold: Minimum similarity to create an edge
            
        Returns:
            KnowledgeGraph object
        """
        logger.info(f"{self.name} building knowledge graph")
        
        graph = KnowledgeGraph()
        
        try:
            # Get all documents
            all_results = self.collection.get(
                include=['embeddings', 'metadatas']
            )
            
            if not all_results['ids']:
                return graph
            
            # Group by document
            documents = {}
            for i, metadata in enumerate(all_results['metadatas']):
                doc_id = metadata.get('document_id')
                if doc_id not in documents:
                    documents[doc_id] = {
                        'name': metadata.get('filename', 'Unknown'),
                        'embedding': all_results['embeddings'][i]
                    }
            
            # Create nodes
            for doc_id, doc_data in documents.items():
                node = KnowledgeNode(
                    id=doc_id,
                    name=doc_data['name'],
                    node_type='document',
                    description=f"Document: {doc_data['name']}"
                )
                graph.add_node(node)
            
            # Create edges based on similarity
            doc_ids = list(documents.keys())
            for i, doc_id1 in enumerate(doc_ids):
                emb1 = np.array(documents[doc_id1]['embedding'])
                
                for doc_id2 in doc_ids[i+1:]:
                    emb2 = np.array(documents[doc_id2]['embedding'])
                    
                    # Calculate similarity
                    similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                    
                    if similarity >= similarity_threshold:
                        edge = KnowledgeEdge(
                            source_id=doc_id1,
                            target_id=doc_id2,
                            relationship='similar_to',
                            weight=float(similarity)
                        )
                        graph.add_edge(edge)
            
            logger.info(f"{self.name} built graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
            return graph
            
        except Exception as e:
            logger.error(f"Error building knowledge graph: {e}")
            return graph
    
    def explain_connection(self, doc_id1: str, doc_id2: str) -> str:
        """
        Use LLM to explain why two documents are related
        
        Args:
            doc_id1: First document ID
            doc_id2: Second document ID
            
        Returns:
            Explanation text
        """
        try:
            # Get sample chunks from each document
            results1 = self.collection.get(
                where={"document_id": doc_id1},
                limit=2,
                include=['documents', 'metadatas']
            )
            
            results2 = self.collection.get(
                where={"document_id": doc_id2},
                limit=2,
                include=['documents', 'metadatas']
            )
            
            if not results1['ids'] or not results2['ids']:
                return "Could not retrieve documents"
            
            doc1_name = results1['metadatas'][0].get('filename', 'Document 1')
            doc2_name = results2['metadatas'][0].get('filename', 'Document 2')
            
            doc1_text = " ".join(results1['documents'][:2])[:1000]
            doc2_text = " ".join(results2['documents'][:2])[:1000]
            
            system_prompt = """You analyze documents and explain their relationships.
Provide a brief, clear explanation of how two documents are related."""
            
            user_prompt = f"""Analyze these two documents and explain how they are related:

Document 1 ({doc1_name}):
{doc1_text}

Document 2 ({doc2_name}):
{doc2_text}

How are these documents related? Provide a concise explanation:"""
            
            explanation = self.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.3,
                max_tokens=256
            )
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error explaining connection: {e}")
            return f"Error: {str(e)}"
