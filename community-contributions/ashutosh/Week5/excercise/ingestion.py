import os
import glob
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
import hashlib
import re

from dotenv import load_dotenv

MODEL = "gpt-4.1-nano"

DB_NAME = str(Path(__file__).parent / "preprocessed_db")
KNOWLEDGE_BASE  = Path(__file__).parent / "docs"


load_dotenv(override=True)

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


def fetch_documents():
    folders = glob.glob(str(Path(KNOWLEDGE_BASE) / "*"))
    documents = []
    for folder in folders:
        doc_type = os.path.basename(folder)
        loader = DirectoryLoader(
            folder, glob="**/*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}
        )
        folder_docs = loader.load()
        for doc in folder_docs:
            doc.metadata["doc_type"] = doc_type
            documents.append(doc)
    print(f"Fetched {len(documents)} documents")
    print(f"Sample document : {documents[0]}")
    print(f"Sample document metadata : {documents[0].metadata}")
    print(f"Sample document content : {documents[0].page_content[:500]}...")
    return documents

import hashlib

def deduplicate_documents(documents):
    seen_hashes = set()
    unique_docs = []

    for doc in documents:
        content_hash = hashlib.md5(
            doc.page_content.strip().encode("utf-8")
        ).hexdigest()

        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            unique_docs.append(doc)

    print(f"Removed {len(documents) - len(unique_docs)} duplicate documents")
    return unique_docs

def create_chunks(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks from {len(documents)} documents")
    print(f"Sample chunk : {chunks[0]}")
    print(f"Sample chunk content : {chunks[0].page_content[:500]}...")
    return chunks


def normalize_text(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def deduplicate_chunks(chunks):
    seen = set()
    unique = []

    for chunk in chunks:
        normalized = normalize_text(chunk.page_content)

        content_hash = hashlib.md5(
            normalized.encode("utf-8")
        ).hexdigest()

        if content_hash not in seen:
            seen.add(content_hash)
            unique.append(chunk)
    print(
        f"Removed {len(chunks) - len(unique)} duplicate chunks"
    )
    return unique

def create_embeddings(chunks):
    if os.path.exists(DB_NAME):
        Chroma(persist_directory=DB_NAME, embedding_function=embeddings).delete_collection()

    vectorstore = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=DB_NAME
    )

    collection = vectorstore._collection
    count = collection.count()

    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
    dimensions = len(sample_embedding)
    print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")
    return vectorstore


if __name__ == "__main__":

    documents = fetch_documents()
    documents = deduplicate_documents(documents)
    chunks = create_chunks(documents)
    chunks = deduplicate_chunks(chunks)
    create_embeddings(chunks)
    print("Ingestion complete")