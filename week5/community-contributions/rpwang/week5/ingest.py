from pathlib import Path
import os
from importlib import import_module

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


load_dotenv(override=True)

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_BASE = ROOT / "knowledge-base"
VECTOR_DB = Path(__file__).resolve().parent / "vector_db"

OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "qwen3-embedding:4b")
HF_EMBEDDING_MODEL = os.getenv(
    "HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)


def get_embeddings():
    provider = os.getenv("EMBEDDING_PROVIDER")
    if not provider:
        provider = "openai" if os.getenv("OPENAI_API_KEY") else "huggingface"
    provider = provider.lower()

    if provider == "openai":
        return OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
    if provider == "ollama":
        ollama_module = import_module("langchain_ollama")
        ollama_embeddings = getattr(ollama_module, "OllamaEmbeddings")
        return ollama_embeddings(model=OLLAMA_EMBEDDING_MODEL)
    if provider == "huggingface":
        hf_module = import_module("langchain_huggingface")
        hf_embeddings = getattr(hf_module, "HuggingFaceEmbeddings")
        return hf_embeddings(model_name=HF_EMBEDDING_MODEL)

    raise ValueError(
        "Unsupported EMBEDDING_PROVIDER. Use one of: openai, ollama, huggingface"
    )


def fetch_documents():
    documents = []
    for folder in KNOWLEDGE_BASE.iterdir():
        if not folder.is_dir():
            continue
        doc_type = folder.name
        loader = DirectoryLoader(
            str(folder),
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        folder_docs = loader.load()
        for doc in folder_docs:
            doc.metadata["doc_type"] = doc_type
            documents.append(doc)
    return documents


def create_chunks(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=140)
    return splitter.split_documents(documents)


def ingest_knowledge_base():
    if not KNOWLEDGE_BASE.exists():
        raise FileNotFoundError(f"Knowledge base path does not exist: {KNOWLEDGE_BASE}")

    embeddings = get_embeddings()
    if VECTOR_DB.exists():
        Chroma(persist_directory=str(VECTOR_DB), embedding_function=embeddings).delete_collection()

    docs = fetch_documents()
    if not docs:
        raise ValueError(f"No markdown documents were found under {KNOWLEDGE_BASE}")

    chunks = create_chunks(docs)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(VECTOR_DB),
    )
    count = vectorstore._collection.count()
    print(
        f"Ingestion complete. Indexed {count:,} chunks into {VECTOR_DB} "
        f"using embedding provider '{os.getenv('EMBEDDING_PROVIDER', 'auto')}'."
    )


if __name__ == "__main__":
    ingest_knowledge_base()
