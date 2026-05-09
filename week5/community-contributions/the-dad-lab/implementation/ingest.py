import os
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, CSVLoader
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


DB_NAME = str(Path(__file__).parent.parent / "activity_db")
KNOWLEDGE_BASE = str(Path(__file__).parent.parent / "datasets")

# embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

embeddings = OllamaEmbeddings(
        model="qwen3-embedding:4b"
    )


def fetch_documents():
    documents = []
    loader = DirectoryLoader(
        KNOWLEDGE_BASE, glob="**/*.csv", loader_cls=CSVLoader, loader_kwargs={"encoding": "utf-8"}
    )
    folder_docs = loader.load()
    for doc in folder_docs:
        documents.append(doc)
    return documents


def create_embeddings(documents):
    # No need to chunk since CSV loader will create a separate document per CSV load
    if os.path.exists(DB_NAME):
        Chroma(persist_directory=DB_NAME, embedding_function=embeddings).delete_collection()

    vectorstore = Chroma.from_documents(
        documents=documents, embedding=embeddings, persist_directory=DB_NAME
    )

    collection = vectorstore._collection
    count = collection.count()

    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
    dimensions = len(sample_embedding)
    print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")
    return vectorstore


if __name__ == "__main__":
    documents = fetch_documents()
    create_embeddings(documents)
    print("Ingestion complete")
