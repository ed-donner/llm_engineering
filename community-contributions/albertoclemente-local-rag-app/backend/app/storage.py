"""
Filesystem operations and document storage management.
Handles secure file operations, metadata persistence, and library organization.
"""

import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import hashlib
import tempfile

from app.models import Document, DocumentType, DocumentStatus
from app.settings import get_settings
from app.diagnostics import get_logger, performance_context

logger = get_logger(__name__)


class SecureFileError(Exception):
    """Custom exception for secure file operations"""
    pass


class DocumentStorage:
    """Manages document storage and metadata persistence"""
    
    def __init__(self):
        self.settings = get_settings()
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.settings.library_raw_dir,
            self.settings.library_parsed_dir,
            self.settings.config_dir,
            self.settings.exports_dir
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    def _get_document_metadata_path(self, doc_id: str) -> Path:
        """Get path to document metadata file"""
        return Path(self.settings.config_dir) / f"doc_{doc_id}.json"
    
    def _get_raw_file_path(self, doc_id: str, filename: str) -> Path:
        """Get path for storing raw uploaded file"""
        # Use doc_id as subdirectory for organization
        doc_dir = Path(self.settings.library_raw_dir) / doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)
        return doc_dir / filename
    
    def _get_parsed_file_path(self, doc_id: str) -> Path:
        """Get path for storing parsed text data"""
        return Path(self.settings.library_parsed_dir) / f"{doc_id}.json"
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for integrity checking"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    async def store_uploaded_file(
        self, 
        file_content: bytes, 
        filename: str, 
        tags: Optional[List[str]] = None
    ) -> Document:
        """
        Store an uploaded file and create document metadata.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            tags: Optional list of tags
            
        Returns:
            Document with metadata
        """
        with performance_context("store_uploaded_file", filename=filename):
            # Determine file type
            file_ext = filename.split('.')[-1].lower()
            # Allow all Docling-supported formats plus legacy formats
            supported_formats = [
                'pdf', 'txt', 'docx', 'md', 'epub', 'pptx', 'html', 'htm',
                'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'asciidoc', 'adoc', 'doc'
            ]
            if file_ext not in supported_formats:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # Calculate file hash BEFORE storing to check for duplicates
            import tempfile
            import hashlib
            
            sha256_hash = hashlib.sha256()
            sha256_hash.update(file_content)
            file_hash = sha256_hash.hexdigest()
            
            # Check for existing document with same hash
            existing_doc = await self.find_duplicate_by_hash(file_hash)
            if existing_doc:
                logger.info(f"Duplicate file detected: {filename} matches existing document {existing_doc.id}")
                # Return the existing document instead of creating a new one
                return existing_doc
            
            # Generate unique document ID
            doc_id = str(uuid.uuid4())
            
            # Store raw file
            raw_file_path = self._get_raw_file_path(doc_id, filename)
            
            try:
                with open(raw_file_path, 'wb') as f:
                    f.write(file_content)
                
                # Create document metadata
                document = Document(
                    id=doc_id,
                    name=filename,
                    type=DocumentType(file_ext),
                    sizeBytes=len(file_content),
                    tags=tags or [],
                    status=DocumentStatus.INDEXING,
                    addedAt=datetime.utcnow()
                )
                
                # Store metadata
                await self._save_document_metadata(document, file_hash)
                
                logger.info(f"Stored document: {doc_id} ({filename})")
                return document
                
            except Exception as e:
                # Clean up on failure
                if raw_file_path.exists():
                    raw_file_path.unlink()
                logger.error(f"Failed to store document {filename}: {e}")
                raise
    
    async def _save_document_metadata(self, document: Document, file_hash: str):
        """Save document metadata to JSON file"""
        metadata_path = self._get_document_metadata_path(document.id)
        
        metadata = {
            **document.model_dump(by_alias=True, mode='json'),
            "file_hash": file_hash,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Saved metadata for document: {document.id}")
    
    async def load_document_metadata(self, doc_id: str) -> Optional[Document]:
        """Load document metadata from storage"""
        metadata_path = self._get_document_metadata_path(doc_id)
        
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Remove internal fields before creating Document
            metadata.pop('file_hash', None)
            metadata.pop('updated_at', None)
            
            # Ensure chunk_count is present with default of 0
            if 'chunk_count' not in metadata:
                metadata['chunk_count'] = 0
            
            return Document(**metadata)
            
        except Exception as e:
            logger.error(f"Failed to load metadata for document {doc_id}: {e}")
            return None
    
    async def find_duplicate_by_hash(self, file_hash: str) -> Optional[Document]:
        """Find existing document with the same file hash"""
        try:
            # Check all document metadata files for matching hash
            config_dir = Path(self.settings.config_dir)
            for metadata_file in config_dir.glob("doc_*.json"):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    if metadata.get('file_hash') == file_hash:
                        # Remove internal fields before creating Document
                        doc_metadata = metadata.copy()
                        doc_metadata.pop('file_hash', None)
                        doc_metadata.pop('updated_at', None)
                        
                        return Document(**doc_metadata)
                        
                except Exception as e:
                    logger.warning(f"Failed to read metadata file {metadata_file}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching for duplicate by hash: {e}")
            return None
    
    async def update_document_metadata(self, doc_id: str, updates: Dict[str, Any]) -> Optional[Document]:
        """Update document metadata"""
        document = await self.load_document_metadata(doc_id)
        if not document:
            return None
        
        # Apply updates with minimal coercion for enums and datetimes
        from datetime import datetime
        from app.models import DocumentStatus, EmbeddingStatus
        for key, value in updates.items():
            if not hasattr(document, key):
                continue
            # Coerce enums if string provided
            if key == "status" and isinstance(value, str):
                try:
                    value = DocumentStatus(value)
                except Exception:
                    pass
            if key == "embedding_status" and isinstance(value, str):
                try:
                    value = EmbeddingStatus(value)
                except Exception:
                    pass
            # Coerce datetimes if ISO string
            if key in {"added_at", "category_generated_at"} and isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except Exception:
                    value = datetime.utcnow()
            setattr(document, key, value)
        
        # Keep original file hash
        metadata_path = self._get_document_metadata_path(doc_id)
        with open(metadata_path, 'r', encoding='utf-8') as f:
            old_metadata = json.load(f)
        file_hash = old_metadata.get('file_hash', '')
        
        await self._save_document_metadata(document, file_hash)
        
        logger.info(f"Updated metadata for document: {doc_id}")
        return document
    
    async def list_documents(
        self, 
        tag_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        category_filter: Optional[str] = None
    ) -> List[Document]:
        """List all documents with optional filters"""
        documents = []
        config_dir = Path(self.settings.config_dir)
        
        for metadata_file in config_dir.glob("doc_*.json"):
            doc_id = metadata_file.stem.replace("doc_", "")
            document = await self.load_document_metadata(doc_id)
            
            if document:
                # Apply filters
                if tag_filter and tag_filter not in document.tags:
                    continue
                if status_filter and document.status != status_filter:
                    continue
                if category_filter and category_filter not in document.categories:
                    continue
                
                documents.append(document)
        
        # Sort by added date (newest first)
        documents.sort(key=lambda d: d.added_at, reverse=True)
        
        logger.debug(f"Listed {len(documents)} documents")
        return documents
    
    async def get_raw_file_path(self, doc_id: str) -> Optional[Path]:
        """Get path to raw file for a document"""
        document = await self.load_document_metadata(doc_id)
        if not document:
            return None
        
        raw_file_path = self._get_raw_file_path(doc_id, document.name)
        if raw_file_path.exists():
            return raw_file_path
        
        return None
    
    async def get_parsed_file_path(self, doc_id: str) -> Path:
        """Get path to parsed file (may not exist yet)"""
        return self._get_parsed_file_path(doc_id)
    
    async def store_parsed_content(self, doc_id: str, parsed_data: Dict[str, Any]):
        """Store parsed document content"""
        parsed_file_path = self._get_parsed_file_path(doc_id)
        
        with open(parsed_file_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Stored parsed content for document: {doc_id}")
    
    async def load_parsed_content(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Load parsed document content"""
        parsed_file_path = self._get_parsed_file_path(doc_id)
        
        if not parsed_file_path.exists():
            return None
        
        try:
            with open(parsed_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load parsed content for document {doc_id}: {e}")
            return None
    
    async def delete_document(self, doc_id: str, secure: bool = False) -> bool:
        """
        Delete a document and all associated files.
        
        Args:
            doc_id: Document identifier
            secure: If True, securely overwrite files before deletion
            
        Returns:
            True if deletion was successful, False if document doesn't exist
        """
        try:
            with performance_context("delete_document", doc_id=doc_id, secure=secure):
                # Check if document exists
                metadata_path = self._get_document_metadata_path(doc_id)
                if not metadata_path.exists():
                    logger.warning(f"Document {doc_id} not found for deletion")
                    return False
                
                # Get file paths
                raw_file_path = await self.get_raw_file_path(doc_id)
                parsed_file_path = self._get_parsed_file_path(doc_id)
                
                # Delete files
                files_to_delete = [metadata_path, parsed_file_path]
                if raw_file_path:
                    files_to_delete.append(raw_file_path)
                
                for file_path in files_to_delete:
                    if file_path.exists():
                        if secure:
                            await self._secure_delete_file(file_path)
                        else:
                            file_path.unlink()
                
                # Remove raw directory if empty
                if raw_file_path:
                    raw_dir = raw_file_path.parent
                    if raw_dir.exists() and not any(raw_dir.iterdir()):
                        raw_dir.rmdir()
                
                logger.info(f"Deleted document: {doc_id} (secure: {secure})")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False
    
    async def _secure_delete_file(self, file_path: Path):
        """Securely delete a file by overwriting it multiple times"""
        if not file_path.exists():
            return
        
        try:
            file_size = file_path.stat().st_size
            
            # Overwrite with random data 3 times
            for _ in range(3):
                with open(file_path, 'r+b') as f:
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            # Finally delete the file
            file_path.unlink()
            
            logger.debug(f"Securely deleted file: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to securely delete {file_path}: {e}")
            # Fall back to regular deletion
            file_path.unlink()
    
    async def export_library(self, export_path: Optional[str] = None) -> str:
        """
        Export the entire document library to a ZIP archive.
        
        Args:
            export_path: Optional custom export path
            
        Returns:
            Path to the created export file
        """
        if not export_path:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            export_filename = f"rag_library_export_{timestamp}.zip"
            export_path = str(Path(self.settings.exports_dir) / export_filename)
        
        with performance_context("export_library"):
            # Create temporary directory for export preparation
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Copy all documents and metadata
                documents = await self.list_documents()
                
                for document in documents:
                    # Copy raw file
                    raw_file_path = await self.get_raw_file_path(document.id)
                    if raw_file_path:
                        dest_dir = temp_path / "raw" / document.id
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(raw_file_path, dest_dir / document.name)
                    
                    # Copy parsed file
                    parsed_file_path = self._get_parsed_file_path(document.id)
                    if parsed_file_path.exists():
                        dest_dir = temp_path / "parsed"
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(parsed_file_path, dest_dir / f"{document.id}.json")
                    
                    # Copy metadata
                    metadata_path = self._get_document_metadata_path(document.id)
                    if metadata_path.exists():
                        dest_dir = temp_path / "metadata"
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(metadata_path, dest_dir / f"doc_{document.id}.json")
                
                # Create ZIP archive
                shutil.make_archive(export_path.replace('.zip', ''), 'zip', temp_dir)
        
        logger.info(f"Exported library to: {export_path}")
        return export_path
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        stats = {
            "total_documents": 0,
            "total_size_bytes": 0,
            "by_type": {},
            "by_status": {}
        }
        
        documents = await self.list_documents()
        
        for document in documents:
            stats["total_documents"] += 1
            stats["total_size_bytes"] += document.size_bytes
            
            # Count by type
            doc_type = document.type
            stats["by_type"][doc_type] = stats["by_type"].get(doc_type, 0) + 1
            
            # Count by status
            doc_status = document.status
            stats["by_status"][doc_status] = stats["by_status"].get(doc_status, 0) + 1
        
        return stats


# Global storage instance
_storage_instance: Optional[DocumentStorage] = None


def get_document_storage() -> DocumentStorage:
    """Get the global document storage instance"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = DocumentStorage()
    return _storage_instance


async def get_document_storage_service() -> DocumentStorage:
    """Get the global document storage service instance (async version)"""
    return get_document_storage()
