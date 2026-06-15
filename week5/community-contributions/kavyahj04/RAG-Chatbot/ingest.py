import os 
import glob
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings 
from dotenv import load_dotenv

load_dotenv(override = True)

MODEL = "GPT-5.4 mini"

DB_NAME = "vector_db"
KNOWLEDGE_BASE = "knowledge_base"

embeddings = OpenAIEmbeddings(model = "text-embedding-3-large")

def fetch_docs():
    folders = glob.glob("knowledge-base/*")
    documents = []
    for folder in folders:
        doc_type = os.path.basename(folder)
        loader = DirectoryLoader(folder, glob = "**/*md", loader_cls = TextLoader, loader_kwargs={"encoding" : "utf-8"})
        folder_docs = loader.load()
        for doc in folder_docs:
            doc.metadata["doc_type"] = doc_type
            documents.append(doc)
    return documents

def create_chunks(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 200)
    chunks = text_splitter.split_documents(documents)
    return chunks

def create_embeddings(chunks):
    if os.path.exists(DB_NAME):
        Chroma(persist_directory = DB_NAME, embedding_function = embeddings).delete_collection()
    vectorstore = Chroma.from_documents(persist_directory = DB_NAME, embedding = embeddings, documents = chunks)

    collection = vectorstore._collection
    count = collection.count()

    sample_emb = collection.get(limit = 1, include = ["embeddings"])["embeddings"][0]
    dimensions = len(sample_emb)
    print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")
    return vectorstore


if __name__ == "__main__":
    documents = fetch_docs()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion Completed")
fetch_docs()