"""
Ingest Medicine and Drug Interaction Data into Vector Store
Processes Medicine_Details.csv and db_drug_interactions.csv
"""
import os
from dotenv import load_dotenv
import pandas as pd
from pathlib import Path
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

def main():
    """Main ingestion function"""

    # Same embeddings as main knowledge base
    embeddings = OpenAIEmbeddings(api_key=api_key, model="text-embedding-3-large")
    # embeddings = HuggingFaceEmbeddings(
    #     model_name="sentence-transformers/all-MiniLM-L6-v2"
    # )

    DB_NAME = str(Path(__file__).parent / "vector_db")
    vectorstore = Chroma(persist_directory=DB_NAME, embedding_function=embeddings)

    print("Loading Medicine Details CSV...")
    medicines_df = pd.read_csv('drugs-knowledge-base/Medicine_Details.csv')
    print(f"Found {len(medicines_df)} medicines in CSV")

    documents = []
    for idx, row in medicines_df.iterrows():
        # Create comprehensive text for embedding
        doc_text = f"""
Medicine Name: {row['Medicine Name']}
Composition: {row['Composition']}
Uses: {row['Uses']}
Side Effects: {row['Side_effects']}
Manufacturer: {row['Manufacturer']}
"""

        doc = Document(
            page_content=doc_text.strip(),
            metadata={
                "doc_type": "drug_info",
                "domain": "pharmacology",
                "medicine_name": row['Medicine Name'],
                "image_url": row['Image URL'],
                "excellent_review": row['Excellent Review %'],
                "average_review": row['Average Review %'],
                "poor_review": row['Poor Review %'],
                "source": "Medicine_Details.csv"
            }
        )
        documents.append(doc)

        if (idx + 1) % 100 == 0:
            print(f"Processed {idx + 1} medicines...")

    # Add medicine documents to vector store
    print(f"\nAdding {len(documents)} medicine documents to vector store...")

    batch_size = 500

    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        vectorstore.add_documents(batch)
        print(f"Inserted {i + len(batch)} / {len(documents)} medicines")

    print(f"✓ Added {len(documents)} medicine documents")

    # Load Drug Interactions CSV
    print("\nLoading Drug Interactions CSV...")
    interactions_df = pd.read_csv('drugs-knowledge-base/db_drug_interactions.csv')
    print(f"Found {len(interactions_df)} drug interactions in CSV")

    interaction_docs = []
    for idx, row in interactions_df.iterrows():
        doc_text = f"""
Drug Interaction between {row['Drug 1']} and {row['Drug 2']}
Description: {row['Interaction Description']}
"""

        doc = Document(
            page_content=doc_text.strip(),
            metadata={
                "doc_type": "drug_interaction",
                "domain": "pharmacology",
                "drug1": row['Drug 1'],
                "drug2": row['Drug 2'],
                "source": "db_drug_interactions.csv"
            }
        )
        interaction_docs.append(doc)

        if (idx + 1) % 1000 == 0:
            print(f"Processed {idx + 1} interactions...")

    # Add interaction documents to vector store
    print(f"\nAdding {len(interaction_docs)} drug interaction documents to vector store...")

    for i in range(0, len(interaction_docs), batch_size):
        batch = interaction_docs[i:i + batch_size]
        vectorstore.add_documents(batch)
        print(f"Inserted {i + len(batch)} / {len(interaction_docs)} interactions")

    print(f"✓ Added {len(interaction_docs)} drug interaction documents")

    print("\n" + "="*60)
    print("✓ Medicine and interaction data ingestion complete!")
    print(f"  - Total medicines: {len(documents)}")
    print(f"  - Total interactions: {len(interaction_docs)}")
    print("="*60)


if __name__ == "__main__":
    main()
