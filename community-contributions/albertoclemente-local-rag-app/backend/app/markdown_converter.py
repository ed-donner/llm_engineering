"""
Markdown conversion utilities using Docling.
Converts various document formats (PDF, DOCX, HTML, PPTX, etc.) to Markdown.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import tempfile
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Docling imports
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logging.warning("Docling not available. Markdown conversion will be disabled.")

from app.diagnostics import get_logger, performance_context

logger = get_logger(__name__)


class MarkdownConversionError(Exception):
    """Custom exception for markdown conversion errors"""
    pass


class MarkdownConverter:
    """Handles document to Markdown conversion using Docling"""
    
    def __init__(self):
        if not DOCLING_AVAILABLE:
            logger.warning("Docling is not available. Markdown conversion will be disabled.")
            self.converter = None
            return
        
        # Set HuggingFace token if available
        hf_token = os.getenv('HF_TOKEN')
        if hf_token:
            os.environ['HF_TOKEN'] = hf_token
            logger.info("HuggingFace token configured for Docling")
        else:
            logger.warning("No HF_TOKEN found - OCR will be disabled")
        
        # Initialize Docling with optimized settings for RAG
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = bool(hf_token)  # Enable OCR if token available
        pipeline_options.do_table_structure = True  # Preserve table structure
        
        if hf_token:
            pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
        
        try:
            self.converter = DocumentConverter(
                allowed_formats=[
                    InputFormat.PDF,
                    InputFormat.DOCX,
                    InputFormat.PPTX,
                    InputFormat.HTML,
                    InputFormat.IMAGE,
                    InputFormat.ASCIIDOC,
                    InputFormat.MD,
                ]
            )
            logger.info(f"Docling MarkdownConverter initialized successfully (OCR: {bool(hf_token)})")
        except Exception as e:
            logger.error(f"Failed to initialize Docling converter: {e}")
            self.converter = None
    
    def is_available(self) -> bool:
        """Check if Docling converter is available"""
        return self.converter is not None
    
    async def convert_to_markdown(self, file_path: Path, preserve_metadata: bool = True) -> Dict[str, Any]:
        """
        Convert a document to Markdown format.
        
        Args:
            file_path: Path to the document file
            preserve_metadata: Whether to include document metadata in the output
            
        Returns:
            Dictionary containing markdown content and metadata
        """
        if not self.is_available():
            raise MarkdownConversionError("Docling converter is not available")
        
        with performance_context("convert_to_markdown", file_type=file_path.suffix):
            logger.info(f"Converting document to Markdown: {file_path.name}")
            
            try:
                # Convert document using Docling
                result = self.converter.convert(str(file_path))
                
                # Extract the converted document
                doc = result.document
                
                # Get markdown content
                markdown_content = doc.export_to_markdown()
                
                # Extract metadata
                metadata = {}
                if preserve_metadata and hasattr(doc, 'metadata'):
                    metadata = {
                        'title': getattr(doc.metadata, 'title', ''),
                        'author': getattr(doc.metadata, 'author', ''),
                        'subject': getattr(doc.metadata, 'subject', ''),
                        'creator': getattr(doc.metadata, 'creator', ''),
                        'creation_date': str(getattr(doc.metadata, 'creation_date', '')),
                    }
                
                # Extract structure information
                structure_info = self._analyze_markdown_structure(markdown_content)
                
                # Count pages if available
                page_count = getattr(doc, 'page_count', None) or len(getattr(doc, 'pages', []))
                
                return {
                    'markdown': markdown_content,
                    'metadata': metadata,
                    'structure': structure_info,
                    'page_count': page_count,
                    'format': file_path.suffix.lstrip('.').lower(),
                    'char_count': len(markdown_content),
                    'word_count': len(markdown_content.split()),
                    'conversion_engine': 'docling'
                }
                
            except Exception as e:
                logger.error(f"Failed to convert {file_path.name} to Markdown: {e}")
                raise MarkdownConversionError(f"Conversion failed: {str(e)}")
    
    def _analyze_markdown_structure(self, markdown: str) -> Dict[str, Any]:
        """Analyze the structure of markdown content"""
        import re
        
        lines = markdown.split('\n')
        
        # Count different structural elements
        headings = re.findall(r'^#{1,6}\s+.+$', markdown, re.MULTILINE)
        lists = re.findall(r'^\s*[-*+]\s+', markdown, re.MULTILINE)
        numbered_lists = re.findall(r'^\s*\d+\.\s+', markdown, re.MULTILINE)
        tables = re.findall(r'\|.*\|', markdown)
        code_blocks = re.findall(r'```[\s\S]*?```', markdown)
        links = re.findall(r'\[([^\]]+)\]\([^)]+\)', markdown)
        
        return {
            'has_headings': len(headings) > 0,
            'heading_count': len(headings),
            'has_lists': len(lists) > 0 or len(numbered_lists) > 0,
            'list_count': len(lists) + len(numbered_lists),
            'has_tables': len(tables) > 0,
            'table_count': len(tables) // 3 if tables else 0,  # Rough estimate
            'has_code_blocks': len(code_blocks) > 0,
            'code_block_count': len(code_blocks),
            'link_count': len(links),
            'total_lines': len(lines),
            'density': 'high' if len(markdown) / max(len(lines), 1) > 80 else 'medium' if len(markdown) / max(len(lines), 1) > 40 else 'low'
        }
    
    def get_supported_formats(self) -> list[str]:
        """Get list of supported file formats"""
        if not self.is_available():
            return []
        
        return [
            'pdf', 'docx', 'pptx', 'html', 'htm',
            'png', 'jpg', 'jpeg', 'tiff', 'bmp',
            'asciidoc', 'adoc', 'md'
        ]


# Global converter instance
_converter_instance: Optional[MarkdownConverter] = None


def get_markdown_converter() -> MarkdownConverter:
    """Get the global markdown converter instance"""
    global _converter_instance
    if _converter_instance is None:
        _converter_instance = MarkdownConverter()
    return _converter_instance


async def get_markdown_converter_service() -> MarkdownConverter:
    """Get the global markdown converter service instance (async version)"""
    return get_markdown_converter()
