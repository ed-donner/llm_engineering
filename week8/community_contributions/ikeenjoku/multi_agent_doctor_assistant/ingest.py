import os
import glob
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

BASE_DIR = Path(__file__).parent

# env_path = Path(__file__).resolve().parents[3] / ".env"
# load_dotenv(env_path)
load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

DB_NAME = str(BASE_DIR / "vector_db")
KNOWLEDGE_BASE = str(BASE_DIR / "knowledge-base")

embeddings = OpenAIEmbeddings(api_key=api_key, model="text-embedding-3-large")
# embeddings = HuggingFaceEmbeddings(
#     model_name="sentence-transformers/all-MiniLM-L6-v2"
# )

def fetch_documents():

    loader = TextLoader(
        str(Path(KNOWLEDGE_BASE) / "clinical_medicine_knowledge.md"),
        encoding="utf-8"
    )

    documents = loader.load()

    for doc in documents:
        doc.metadata["doc_type"] = "clinical_medicine"

    print(f"Loaded {len(documents)} documents")

    return documents


def detect_domain(text):
    """Detect medical domain from text content"""
    text_lower = text.lower()

    # Domain keyword mapping
    domain_keywords = {
        "cardiology": [
            "heart", "cardiac", "cardiovascular", "ecg", "echocardiography",
            "myocardial", "coronary", "arrhythmia", "atrial", "ventricular",
            "cardiomyopathy", "pericardial", "endocarditis", "angina"
        ],
        "neurology": [
            "brain", "neurological", "nervous system", "neuro", "cerebral",
            "stroke", "seizure", "epilepsy", "dementia", "parkinson",
            "migraine", "neuropathy", "consciousness", "cranial"
        ],
        "pharmacology": [
            "drug", "medication", "dosage", "pharmaceutical", "prescription",
            "pharmacology", "adverse effect", "side effect", "contraindication",
            "interaction", "therapy", "treatment", "dose"
        ],
        "gastroenterology": [
            "digestive", "stomach", "gastrointestinal", "gi", "intestinal",
            "bowel", "liver", "hepatic", "pancreas", "oesophageal", "gastric",
            "colitis", "crohn", "ulcer", "diarrhea", "constipation"
        ],
        "infectious_disease": [
            "infection", "antibiotic", "bacterial", "viral", "fungal",
            "sepsis", "pneumonia", "tuberculosis", "hiv", "meningitis",
            "abscess", "cellulitis", "fever", "pathogen"
        ],
        "oncology": [
            "cancer", "tumor", "tumour", "chemotherapy", "oncology",
            "malignancy", "carcinoma", "lymphoma", "leukemia", "metastasis",
            "radiotherapy", "neoplasm", "biopsy"
        ],
        "rheumatology": [
            "arthritis", "joint", "rheumatoid", "lupus", "autoimmune",
            "inflammation", "connective tissue", "musculoskeletal",
            "osteoarthritis", "gout", "vasculitis"
        ]
    }

    # Count matches for each domain
    domain_scores = {}
    for domain, keywords in domain_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            domain_scores[domain] = score

    # Return domain with highest score, or general_medicine as default
    if domain_scores:
        return max(domain_scores, key=domain_scores.get)
    return "general_medicine"


def create_chunks(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150
    )

    chunks = splitter.split_documents(documents)

    # Add domain metadata to each chunk
    for chunk in chunks:
        domain = detect_domain(chunk.page_content)
        chunk.metadata["domain"] = domain

    print(f"Created {len(chunks)} chunks with domain metadata")

    return chunks


def create_embeddings(chunks):

    if os.path.exists(DB_NAME):
        Chroma(
            persist_directory=DB_NAME,
            embedding_function=embeddings
        ).delete_collection()

    batch_size = 200
    vectorstore = None

    for i in range(0, len(chunks), batch_size):

        batch = chunks[i:i + batch_size]

        texts = [doc.page_content for doc in batch]
        metadatas = [doc.metadata for doc in batch]

        if vectorstore is None:
            vectorstore = Chroma.from_texts(
                texts=texts,
                metadatas=metadatas,
                embedding=embeddings,
                persist_directory=DB_NAME
            )
        else:
            vectorstore.add_texts(texts, metadatas)

        print(f"Processed {i + len(batch)} / {len(chunks)} chunks")

    collection = vectorstore._collection

    count = collection.count()

    sample_embedding = collection.get(
        limit=1,
        include=["embeddings"]
    )["embeddings"][0]

    dimensions = len(sample_embedding)

    print(f"There are {count:,} vectors stored")
    print(f"Embedding dimensions: {dimensions}")

    return vectorstore


if __name__ == "__main__":

    documents = fetch_documents()

    chunks = create_chunks(documents)

    create_embeddings(chunks)

    print("Clinical medicine knowledge ingestion complete")