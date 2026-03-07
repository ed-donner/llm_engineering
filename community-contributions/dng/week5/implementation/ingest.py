import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from huggingface_hub import snapshot_download

MODEL = "gpt-4.1-nano"

DB_NAME = str(Path(__file__).parent.parent / "vector_db")
KNOWLEDGE_BASE = snapshot_download(
    repo_id="gathondu/east-logistics",
    repo_type="dataset",
)
load_dotenv(override=True)

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")


def create_row_documents():
    documents = []

    for file in os.listdir(KNOWLEDGE_BASE):
        if not file.endswith(".csv"):
            continue

        file_path = os.path.join(KNOWLEDGE_BASE, file)
        df = pd.read_csv(file_path)

        for idx, row in df.iterrows():
            # Build a canonical text representation of the row
            row_text = " | ".join([f"{col}:{row[col]}" for col in df.columns])

            # Store metadata for easy filtering later
            metadata = {col: row[col] for col in df.columns}
            metadata["source_file"] = file
            metadata["row_id"] = idx  # optional unique id

            documents.append(Document(page_content=row_text, metadata=metadata))

    return documents


def create_embeddings(documents):
    if os.path.exists(DB_NAME):
        Chroma(
            persist_directory=DB_NAME, embedding_function=embeddings
        ).delete_collection()

    vectorstore = Chroma.from_documents(
        documents=documents, embedding=embeddings, persist_directory=DB_NAME
    )

    collection = vectorstore._collection
    count = collection.count()
    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]  # ty:ignore[not-subscriptable]
    dimensions = len(sample_embedding)

    print(
        f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store"
    )
    return vectorstore


if __name__ == "__main__":
    documents = create_row_documents()
    create_embeddings(documents)
    print("Ingestion complete")
