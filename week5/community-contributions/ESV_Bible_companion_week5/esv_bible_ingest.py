import os
import glob
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings


from dotenv import load_dotenv


DB_NAME = "esv_bible_db"
KNOWLEDGE_BASE = str(Path(__file__).parent.parent / "ESV_Bible")

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

load_dotenv(override=True)


def fetch_books():
    print(f"Fetching books from {KNOWLEDGE_BASE}")
    folders = glob.glob(str(Path(KNOWLEDGE_BASE) / "*"))
    books = []
    for folder in folders:
        book = os.path.basename(folder)
        loader = DirectoryLoader(
            folder, glob="**/*.md", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}
        )
        folder_docs = loader.load()
        for doc in folder_docs:
            doc.metadata["book"] = book
            books.append(doc)
    return books


def create_chunks(books):
    print(f"Creating chunks from {len(books)} books")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
    chunks = text_splitter.split_documents(books)
    return chunks


def create_embeddings(chunks):
    print(f"Creating embeddings from {len(chunks)} chunks")
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
    print("Starting Bible Ingestion")
    books = fetch_books()
    chunks = create_chunks(books)
    create_embeddings(chunks)
    print("Ingestion complete")
