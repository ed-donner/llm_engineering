import os
import glob
from pathlib import Path
from langchain_community.document_loaders import UnstructuredEPubLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


from dotenv import load_dotenv

DB_NAME = str(Path(__file__).parent.parent / "vector_db_bookstore")
KNOWLEDGE_BASE = str(Path(__file__).parent.parent / "knowledge-base")
print(DB_NAME)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

load_dotenv(override=True)


def fetch_documents():
    epub_pattern = str(Path(KNOWLEDGE_BASE) / "**" / "*.epub")
    epub_files = glob.glob(epub_pattern, recursive=True)
    documents = []
    for file_path in epub_files:
        loader = UnstructuredEPubLoader(file_path, mode="single")
        documents.extend(loader.load())
    return documents


def create_chunks(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, length_function=len)
    chunks = text_splitter.split_documents(documents)
    return chunks


def create_embeddings(chunks):
    if os.path.exists(DB_NAME):
        Chroma(persist_directory=DB_NAME,
               embedding_function=embeddings).delete_collection()
    vectorstore = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=DB_NAME
    )
    return vectorstore


if __name__ == "__main__":
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete")
