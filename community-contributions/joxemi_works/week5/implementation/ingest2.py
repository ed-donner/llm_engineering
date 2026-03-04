"""
ULTRA DUMMIE DESCRIPTION
------------------------
What this file does:
- Prepares the RAG "memory".
- Reads all .md files from knowledge-base.
- Splits text into small chunks.
- Converts each chunk into numbers (embeddings).
- Saves everything into vector_db for fast search later.

Internal steps:
1) Loads variables and configures the embedding model (HuggingFace).
2) Iterates through knowledge-base folders and loads documents.
3) Adds doc_type metadata based on folder name (employees, contracts, etc.).
4) Splits documents into chunks with overlap.
5) Deletes previous index if it exists and creates a new one in Chroma.
6) Prints how many vector rows were stored.

Key logic:
- This file does NOT answer questions.
- It only indexes knowledge so answer2.py can retrieve it later.
"""

import os  # Imports operating system utilities for paths and checks.
import glob  # Imports pattern-based search for files/folders.
from pathlib import Path  # Imports Path objects to handle paths robustly.
from langchain_community.document_loaders import DirectoryLoader, TextLoader  # Imports document loaders for folders and plain text.
from langchain_text_splitters import RecursiveCharacterTextSplitter  # Imports splitter to break long text into chunks.
from langchain_chroma import Chroma  # Imports integration with Chroma vector database.
from langchain_huggingface import HuggingFaceEmbeddings  # Imports free HuggingFace embeddings.


from dotenv import load_dotenv  # Imports function to load environment variables from .env.

#EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Defines free HuggingFace embedding model.
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

CHUNK_SIZE = 700  # Defines chunk size used when splitting documents.
CHUNK_OVERLAP = 150  # Defines chunk overlap used when splitting documents.
DEBUG = True  # Enables or disables debug logs to trace the flow.

DB_NAME = str(Path(__file__).parent.parent / "vector_db")  # Builds the path where the vector database will be stored.
KNOWLEDGE_BASE = str(Path(__file__).parent.parent / "knowledge-base")  # Builds the path where source documents are located.

load_dotenv(override=True)  # Loads environment variables and allows overwriting existing ones.

embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)  # Initializes the local HuggingFace model for text-to-vector conversion.


def dbg(message):  # Defines helper to print traces only when DEBUG is active.
    if DEBUG:  # Checks debug flag.
        print(f"[INGEST] {message}")  # Prints log with module prefix.


def fetch_documents():  # Defines function to load documents from the knowledge base.
    folders = glob.glob(str(Path(KNOWLEDGE_BASE) / "*"))  # Lists all subfolders inside knowledge-base.
    dbg(f"Detected folders: {len(folders)}")  # Traces number of detected folders.
    documents = []  # Initializes empty list to accumulate loaded documents.
    for folder in folders:  # Iterates through each detected subfolder.
        doc_type = os.path.basename(folder)  # Extracts folder name to use as document type.
        dbg(f"Reading folder: {folder} (doc_type={doc_type})")  # Traces folder and document type.
        loader = DirectoryLoader(  # Creates loader to read files from current folder.
            folder, glob="**/*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}  # Configures recursive .md reading in UTF-8.
        )  # Closes DirectoryLoader configuration.
        folder_docs = loader.load()  # Loads documents from folder into LangChain Document format.
        dbg(f"Documents loaded in folder: {len(folder_docs)}")  # Traces how many docs were loaded from that folder.
        for doc in folder_docs:  # Iterates through each loaded document in the folder.
            doc.metadata["doc_type"] = doc_type  # Adds metadata with document type for traceability.
            documents.append(doc)  # Adds document to global list.
    dbg(f"Total accumulated documents: {len(documents)}")  # Traces total documents for indexing.
    return documents  # Returns all collected documents.


def create_chunks(documents):  # Defines function to split long documents into fragments.
    dbg(f"Creating chunks for {len(documents)} documents")  # Traces number of input documents.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)  # Configures chunk splitting strategy from constants.
    chunks = text_splitter.split_documents(documents)  # Applies splitting and generates chunks list.
    dbg(f"Chunks created: {len(chunks)}")  # Traces number of resulting chunks.
    total = len(chunks)  # Stores total number of chunks to select head/tail previews.
    if total <= 10:  # If there are few chunks, print all previews once.
        for i, chunk in enumerate(chunks, start=1):  # Iterates through each chunk.
            preview = chunk.page_content[:100].replace("\n", " ")  # Keeps first 100 characters and flattens line breaks.
            dbg(f"Chunk {i} preview (100 chars): {preview}")  # Prints preview for each chunk.
    else:  # If there are many chunks, print only first 5 and last 5 previews.
        for i, chunk in enumerate(chunks[:5], start=1):  # Iterates through first five chunks.
            preview = chunk.page_content[:100].replace("\n", " ")  # Keeps first 100 characters and flattens line breaks.
            dbg(f"Chunk {i} preview (100 chars): {preview}")  # Prints preview for each head chunk.
        dbg("... skipping middle chunks ...")  # Prints separator to indicate omitted middle chunks.
        for offset, chunk in enumerate(chunks[-5:], start=total - 4):  # Iterates through last five chunks with original positions.
            preview = chunk.page_content[:100].replace("\n", " ")  # Keeps first 100 characters and flattens line breaks.
            dbg(f"Chunk {offset} preview (100 chars): {preview}")  # Prints preview for each tail chunk.
    return chunks  # Returns resulting chunks.


def create_embeddings(chunks):  # Defines function to create and persist embeddings in Chroma.
    dbg(f"Inserting {len(chunks)} chunks into vector store")  # Traces data volume to vectorize.
    if os.path.exists(DB_NAME):  # Checks whether a previous vector database exists on disk.
        dbg("Previous database detected. Deleting existing collection")  # Traces collection reset.
        Chroma(persist_directory=DB_NAME, embedding_function=embeddings).delete_collection()  # Deletes previous collection to reindex from scratch.

    vectorstore = Chroma.from_documents(  # Creates a new vector store from chunks.
        documents=chunks, embedding=embeddings, persist_directory=DB_NAME  # Passes documents, embedding model, and persistence path.
    )  # Closes vector store creation.

    collection = vectorstore._collection  # Accesses internal collection for inspection.
    count = collection.count()  # Counts how many vectors were stored.

    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]  # Retrieves one sample embedding from the collection.
    dimensions = len(sample_embedding)  # Calculates embedding vector size (dimension).
    dbg(f"Vector store ready with {count} vectors and dimension {dimensions}")  # Traces technical index summary.
    print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")  # Prints vector count and dimensionality summary.
    return vectorstore  # Returns created vector store.


if __name__ == "__main__":  # Runs this block only when file is executed directly.
    dbg("Ingestion start")  # Traces script execution start.
    dbg(f"KNOWLEDGE_BASE={KNOWLEDGE_BASE}")  # Traces source knowledge path.
    dbg(f"DB_NAME={DB_NAME}")  # Traces vector persistence path.
    dbg(f"EMBEDDING_MODEL={EMBEDDING_MODEL}")  # Traces configured embedding model.
    documents = fetch_documents()  # Step 1: loads documents from knowledge-base.
    chunks = create_chunks(documents)  # Step 2: splits documents into chunks.
    create_embeddings(chunks)  # Step 3: generates embeddings and stores them in vector database.
    print("Ingestion complete")  # Shows final message when ingestion ends.
