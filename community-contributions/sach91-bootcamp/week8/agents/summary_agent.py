"""
Summary Agent - Creates summaries and extracts key points from documents
"""
import logging
from typing import Dict, List
from agents.base_agent import BaseAgent
from models.document import Summary
import chromadb

logger = logging.getLogger(__name__)

class SummaryAgent(BaseAgent):
    """Agent that creates summaries of documents"""
    
    def __init__(self, collection: chromadb.Collection,
                 llm_client=None, model: str = "llama3.2"):
        """
        Initialize summary agent
        
        Args:
            collection: ChromaDB collection with documents
            llm_client: Optional shared LLM client
            model: Ollama model name
        """
        super().__init__(name="SummaryAgent", llm_client=llm_client, model=model)
        self.collection = collection
        
        logger.info(f"{self.name} initialized")
    
    def process(self, document_id: str = None, document_text: str = None, 
                document_name: str = "Unknown") -> Summary:
        """
        Create a summary of a document
        
        Args:
            document_id: ID of document in ChromaDB (retrieves chunks if provided)
            document_text: Full document text (used if document_id not provided)
            document_name: Name of the document
            
        Returns:
            Summary object
        """
        logger.info(f"{self.name} creating summary for: {document_name}")
        
        # Get document text
        if document_id:
            text = self._get_document_text(document_id)
            if not text:
                return Summary(
                    document_id=document_id,
                    document_name=document_name,
                    summary_text="Error: Could not retrieve document",
                    key_points=[]
                )
        elif document_text:
            text = document_text
        else:
            return Summary(
                document_id="",
                document_name=document_name,
                summary_text="Error: No document provided",
                key_points=[]
            )
        
        # Truncate if too long (to fit in context)
        max_chars = 8000
        if len(text) > max_chars:
            logger.warning(f"{self.name} truncating document from {len(text)} to {max_chars} chars")
            text = text[:max_chars] + "\n\n[Document truncated...]"
        
        # Generate summary
        summary_text = self._generate_summary(text)
        
        # Extract key points
        key_points = self._extract_key_points(text)
        
        summary = Summary(
            document_id=document_id or "",
            document_name=document_name,
            summary_text=summary_text,
            key_points=key_points
        )
        
        logger.info(f"{self.name} completed summary with {len(key_points)} key points")
        return summary
    
    def _get_document_text(self, document_id: str) -> str:
        """Retrieve and reconstruct document text from chunks"""
        try:
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if not results['ids']:
                return ""
            
            # Sort by chunk index
            chunks_data = list(zip(
                results['documents'],
                results['metadatas']
            ))
            
            chunks_data.sort(key=lambda x: x[1].get('chunk_index', 0))
            
            # Combine chunks
            text = "\n\n".join([chunk[0] for chunk in chunks_data])
            return text
            
        except Exception as e:
            logger.error(f"Error retrieving document: {e}")
            return ""
    
    def _generate_summary(self, text: str) -> str:
        """Generate a concise summary of the text"""
        system_prompt = """You are an expert at creating concise, informative summaries.
Your summaries capture the main ideas and key information in clear, accessible language.
Keep summaries to 3-5 sentences unless the document is very long."""
        
        user_prompt = f"""Please create a concise summary of the following document:

{text}

Summary:"""
        
        summary = self.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.3,
            max_tokens=512
        )
        
        return summary.strip()
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from the text"""
        system_prompt = """You extract the most important key points from documents.
List 3-7 key points as concise bullet points. Each point should be a complete, standalone statement."""
        
        user_prompt = f"""Please extract the key points from the following document:

{text}

List the key points (one per line, without bullets or numbers):"""
        
        response = self.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.3,
            max_tokens=512
        )
        
        # Parse the response into a list
        key_points = []
        for line in response.split('\n'):
            line = line.strip()
            # Remove common list markers
            line = line.lstrip('•-*0123456789.)')
            line = line.strip()
            
            if line and len(line) > 10:  # Filter out very short lines
                key_points.append(line)
        
        return key_points[:7]  # Limit to 7 points
    
    def summarize_multiple(self, document_ids: List[str]) -> List[Summary]:
        """
        Create summaries for multiple documents
        
        Args:
            document_ids: List of document IDs
            
        Returns:
            List of Summary objects
        """
        summaries = []
        
        for doc_id in document_ids:
            summary = self.process(document_id=doc_id)
            summaries.append(summary)
        
        return summaries
