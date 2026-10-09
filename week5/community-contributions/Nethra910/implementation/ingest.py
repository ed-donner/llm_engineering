import os
import glob
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


from dotenv import load_dotenv
load_dotenv(override=True)


KNOWLEDGE_BASE = str(Path(__file__).parent.parent / "knowledge_base")
DB_NAME = str(Path(__file__).parent.parent / "vector_db")

embeddings = HuggingFaceEmbeddings(model_name = "all-MiniLM-L6-v2")


def fetch_documents():
    loader = DirectoryLoader(
        str(KNOWLEDGE_BASE),
        glob="*.pdf",
        loader_cls=PyPDFLoader
    )

    documents = loader.load()

    return documents

def create_chunks(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 200
    )
    chunks = text_splitter.split_documents(documents)
    return chunks


def create_embeddings(chunks):
    if os.path.exists(DB_NAME):
        Chroma(
            persist_directory=str(DB_NAME),
            embedding_function=embeddings
        ).delete_collection()

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(DB_NAME)
    )
    collection = vectorstore._collection
    count = collection.count()
    sample_embedding = collection.get(
        limit=1,
        include=["embeddings"]
    )["embeddings"][0]
    dimensions = len(sample_embedding)
    print(
        f"There are {count:,} vectors "
        f"with {dimensions:,} dimensions in the vector store"
    )
    return vectorstore


if __name__ == "__main__":
    print("Loading documents...")
    documents = fetch_documents()
    print(f"Loaded {len(documents)} documents")

    print("\nCreating chunks...")
    chunks = create_chunks(documents)
    print(f"Created {len(chunks)} chunks")

    print("\nCreating embeddings and vector store...")
    vectorstore = create_embeddings(chunks)

    print("\nIngestion completed successfully!")