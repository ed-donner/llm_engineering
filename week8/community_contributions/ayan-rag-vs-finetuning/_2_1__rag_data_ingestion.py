from huggingface_hub import login
from dotenv import load_dotenv
import os
from datasets import load_dataset
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


load_dotenv(override=True)
hf_token = os.getenv('HF_TOKEN')
login(token=hf_token)

ds = load_dataset("ayanmukherjee/repliqa-4-company-policies-answerable")


documents = []

for split in ds: 
    for item in ds[split]:

        documents.append(
            Document(
                page_content=item.get("document_extracted", "").strip(),
                metadata={
                    "document_id": item.get("document_id"),
                    "topic": item.get("document_topic"),
                    "source": item.get("document_path")
                }
            )
        )


splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = splitter.split_documents(documents)


embeddings = HuggingFaceEmbeddings(model_name="google/embeddinggemma-300m")
DB_NAME = "chroma_langchain_db"

if os.path.exists(DB_NAME):
    Chroma(embedding_function=embeddings, persist_directory=DB_NAME).delete_collection()

vector_store = Chroma(
    collection_name="context_collection",
    embedding_function=embeddings,
    persist_directory=DB_NAME
)

vector_store.add_documents(documents=chunks)
print(f"Vectorstore created with {vector_store._collection.count()} documents")
