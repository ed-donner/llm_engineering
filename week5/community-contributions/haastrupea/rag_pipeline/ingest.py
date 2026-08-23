import os
import glob
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings


from dotenv import load_dotenv

MODEL = "gpt-4.1-nano"

DB_NAME = str(Path(__file__).parent.parent / "vector_db")
KNOWLEDGE_BASE = str(Path(__file__).parent.parent / "knowledge-base")
openrouter_url = "https://openrouter.ai/api/v1"
# embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

load_dotenv(override=True)

api_key = os.getenv('OPENAI_API_KEY')

embeddings = OpenAIEmbeddings(model="text-embedding-3-large", base_url=openrouter_url, api_key=api_key)


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
    return documents


def create_chunks(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    return chunks


def create_embeddings(chunks, db_path: str = None):
    path = db_path or DB_NAME
    if os.path.exists(path):
        Chroma(persist_directory=path, embedding_function=embeddings).delete_collection()

    vectorstore = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=path
    )

    collection = vectorstore._collection
    count = collection.count()

    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
    dimensions = len(sample_embedding)
    print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")
    return vectorstore


def scrape_and_ingest(url: str, db_path: str = None):
    """
    Scrape URL, create Documents, chunk, embed, store in Chroma.
    Returns vectorstore for use by the answer module.
    """
    from langchain_core.documents import Document

    from .scraper import get_web_content_sync

    text = get_web_content_sync(url)
    documents = [Document(page_content=text, metadata={"source": url})]
    chunks = create_chunks(documents)
    return create_embeddings(chunks, db_path or DB_NAME)


if __name__ == "__main__":
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete")
