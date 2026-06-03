# ingest.py
import os
import glob
import gdown
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Import constants
from config import DB_NAME, DEVICE, KNOWLEDGE_BASE, DRIVE_FOLDER_URL, EMBEDDING_MODEL

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={'device': DEVICE},   
    encode_kwargs={'normalize_embeddings': True}
)

def sync_google_drive():
    print("Syncing manuals from Google Drive...")
    os.makedirs(KNOWLEDGE_BASE, exist_ok=True)
    
    gdown.download_folder(url=DRIVE_FOLDER_URL, output=KNOWLEDGE_BASE, quiet=False, use_cookies=False)
    print("Google Drive sync complete.\n")

def fetch_documents():
    sync_google_drive()
    
    pdf_files = glob.glob(f"{KNOWLEDGE_BASE}/**/*.pdf", recursive=True)
    documents = []
    
    print(f"Found {len(pdf_files)} PDF manuals to process in the local cache.")
    
    for file in pdf_files:
        print(f"Loading: {os.path.basename(file)}...")
        loader = PyPDFLoader(file)
        docs = loader.load()
        
        doc_name = os.path.basename(file).replace('.pdf', '')
        
        for doc in docs:
            doc.metadata["source_manual"] = doc_name
            page_num = doc.metadata.get('page', 'Unknown')
            
            doc.page_content = f"Source Manual: {doc_name}\nPage: {page_num}\n\n{doc.page_content}"
            
        documents.extend(docs)
        
    print(f"Loaded a total of {len(documents)} pages.")
    return documents

def create_chunks(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks):,} chunks from the documents.")
    return chunks

def create_embeddings(chunks):
    if os.path.exists(DB_NAME):
        print("Clearing existing vector database...")
        Chroma(persist_directory=DB_NAME, embedding_function=embeddings).delete_collection()

    print("Generating local embeddings and saving to Chroma. This will take some compute time...")
    vectorstore = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=DB_NAME
    )

    collection = vectorstore._collection
    count = collection.count()

    print(f"Success! There are {count:,} vectors stored in the database.")
    return vectorstore

def run_ingestion():
    """Runs the full document fetching, chunking, and embedding pipeline."""
    print("Starting automated ingestion process...")
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete.")

if __name__ == "__main__":
    run_ingestion()