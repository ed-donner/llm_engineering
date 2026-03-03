import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_openai import OpenAIEmbeddings

MODEL = "gpt-4.1-nano"

DB_NAME = str(Path(__file__).parent.parent / "vector_db")
KNOWLEDGE_BASE = str(Path(__file__).parent.parent / "knowledge-base")

load_dotenv(override=True)

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")


def create_chunks():
    loaders = []
    for file in os.listdir(KNOWLEDGE_BASE):
        file_path = os.path.join(KNOWLEDGE_BASE, file)
        df = pd.read_csv(file_path)
        source_col = df.columns[0]
        loader = CSVLoader(
            file_path, source_column=source_col, metadata_columns=[source_col]
        )
        loaders.extend(loader.load())
    return loaders


def create_embeddings(chunks):
    if os.path.exists(DB_NAME):
        Chroma(
            persist_directory=DB_NAME, embedding_function=embeddings
        ).delete_collection()

    vectorstore = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=DB_NAME
    )

    collection = vectorstore._collection
    count = collection.count()

    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
    dimensions = len(sample_embedding)
    print(
        f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store"
    )
    return vectorstore


if __name__ == "__main__":
    chunks = create_chunks()
    create_embeddings(chunks)
    print("Ingestion complete")
