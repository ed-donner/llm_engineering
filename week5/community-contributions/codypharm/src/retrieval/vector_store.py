import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Literal
from src.processing.chunker import Chunk
import os
from dotenv import load_dotenv

class PharmaVectorStore:
    def __init__(
        self, 
        collection_name: str = "pharma_rag",
        embedding_type: Literal["openai", "bge", "biobert", "default"] = "openai"
    ):
        load_dotenv()
        
        if embedding_type == "openai":
            self.ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.getenv("OPENAI_API_KEY"),
                model_name="text-embedding-3-small"
            )
        elif embedding_type == "bge":
            self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="BAAI/bge-large-en-v1.5"
            )
        elif embedding_type == "biobert":
            self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb"
            )
        else:
            self.ef = embedding_functions.DefaultEmbeddingFunction()
        
        self.client = chromadb.PersistentClient(path="./data/chroma_db")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef
        )

    def add_chunks(self, chunks: List[Chunk], summaries: List[str] = None):
        if not chunks:
            return
        
        if summaries:
            if len(summaries) != len(chunks):
                raise ValueError(f"Summaries ({len(summaries)}) must match chunks ({len(chunks)})")
            documents = summaries
            metadatas = []
            for c in chunks:
                meta = c.metadata.copy()
                meta["raw_content"] = c.page_content
                metadatas.append(meta)
        else:
            documents = [c.page_content for c in chunks]
            metadatas = [c.metadata for c in chunks]
        
        ids = [
            f"{c.metadata.get('drug_name', 'unknown')}_{c.metadata.get('section', 'unknown')}_{i}"
            for i, c in enumerate(chunks)
        ]
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def search(self, query: str, k: int = 3) -> Dict[str, Any]:
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        return results
    
    def reset(self):
        self.client.delete_collection(name=self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            embedding_function=self.ef
        )