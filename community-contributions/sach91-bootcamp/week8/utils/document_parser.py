"""
Document Parser - Extract text from various document formats
"""
import os
from typing import List, Dict, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DocumentParser:
    """Parse various document formats into text chunks"""
    
    SUPPORTED_FORMATS = ['.pdf', '.docx', '.txt', '.md', '.html', '.py']
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize document parser
        
        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks for context preservation
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def parse_file(self, file_path: str) -> Dict:
        """
        Parse a file and return structured document data
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with document metadata and chunks
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        extension = path.suffix.lower()
        
        if extension not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {extension}")
        
        # Extract text based on file type
        if extension == '.pdf':
            text = self._parse_pdf(file_path)
        elif extension == '.docx':
            text = self._parse_docx(file_path)
        elif extension == '.txt' or extension == '.py':
            text = self._parse_txt(file_path)
        elif extension == '.md':
            text = self._parse_markdown(file_path)
        elif extension == '.html':
            text = self._parse_html(file_path)
        else:
            text = ""
        
        # Create chunks
        chunks = self._create_chunks(text)
        
        return {
            'filename': path.name,
            'filepath': str(path.absolute()),
            'extension': extension,
            'text': text,
            'chunks': chunks,
            'num_chunks': len(chunks),
            'total_chars': len(text)
        }
    
    def _parse_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(file_path)
            text = ""
            
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            
            return text.strip()
        
        except ImportError:
            logger.error("pypdf not installed. Install with: pip install pypdf")
            return ""
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            return ""
    
    def _parse_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            text = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            
            return text.strip()
        
        except ImportError:
            logger.error("python-docx not installed. Install with: pip install python-docx")
            return ""
        except Exception as e:
            logger.error(f"Error parsing DOCX: {e}")
            return ""
    
    def _parse_txt(self, file_path: str) -> str:
        """Extract text from TXT"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error parsing TXT: {e}")
            return ""
    
    def _parse_markdown(self, file_path: str) -> str:
        """Extract text from Markdown"""
        try:
            import markdown
            from bs4 import BeautifulSoup
            
            with open(file_path, 'r', encoding='utf-8') as f:
                md_text = f.read()
            
            # Convert markdown to HTML then extract text
            html = markdown.markdown(md_text)
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()
            
            return text.strip()
        
        except ImportError:
            # Fallback: just read as plain text
            return self._parse_txt(file_path)
        except Exception as e:
            logger.error(f"Error parsing Markdown: {e}")
            return ""
    
    def _parse_html(self, file_path: str) -> str:
        """Extract text from HTML"""
        try:
            from bs4 import BeautifulSoup
            
            with open(file_path, 'r', encoding='utf-8') as f:
                html = f.read()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text.strip()
        
        except ImportError:
            logger.error("beautifulsoup4 not installed. Install with: pip install beautifulsoup4")
            return ""
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return ""
    
    def _create_chunks(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Full text to chunk
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            logger.info(f'Processing chunk at {start}, for len {text_length}.')

            end = start + self.chunk_size
            
            # If this isn't the last chunk, try to break at a sentence or paragraph
            if end < text_length:
                # Look for paragraph break first
                break_pos = text.rfind('\n\n', start, end)
                if break_pos == -1:
                    # Look for sentence break
                    break_pos = text.rfind('. ', start, end)
                if break_pos == -1:
                    # Look for any space
                    break_pos = text.rfind(' ', start, end)
                
                if break_pos != -1 and break_pos > start and break_pos > end - self.chunk_overlap:
                    end = break_pos + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start < 0:
                start = 0
        
        return chunks
