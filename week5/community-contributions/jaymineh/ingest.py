import os
import glob
from pathlib import Path
from collections import defaultdict
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from litellm import completion
from dotenv import load_dotenv

MODEL = "openrouter/openai/gpt-4o-mini"

DB_NAME = str(Path(__file__).parent.parent / "vector_db")
KNOWLEDGE_BASE = str(Path(__file__).parent.parent / "knowledge-base")

load_dotenv(override=True)

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    encode_kwargs={"normalize_embeddings": True},
)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)


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
    return text_splitter.split_documents(documents)


def generate_document_summary(doc):
    source = doc.metadata.get("source", "unknown")
    doc_type = doc.metadata.get("doc_type", "unknown")
    text = doc.page_content[:8000]

    messages = [
        {"role": "user", "content": f"""Summarize this {doc_type} document from Insurellm's knowledge base.
Capture ALL key facts: full names, titles, numbers, dates, roles, relationships, and important details.
Include specific searchable terms that someone might query for.
Source: {source}

Document:
{text}

Comprehensive summary:"""}
    ]
    response = completion(model=MODEL, messages=messages)
    return Document(
        page_content=f"Summary of {source}:\n\n{response.choices[0].message.content}",
        metadata={"doc_type": doc_type, "source": source, "is_summary": "true"},
    )


def generate_category_summary(category, docs):
    combined = "\n\n---\n\n".join(
        f"Source: {doc.metadata.get('source', 'unknown')}\n{doc.page_content[:2000]}"
        for doc in docs
    )
    if len(combined) > 25000:
        combined = combined[:25000]

    messages = [
        {"role": "user", "content": f"""Create a comprehensive overview of ALL {category} at Insurellm.
List every person, product, contract, or detail mentioned with key facts about each.
Include full names, titles, dates, numbers, and relationships.
This overview will be used to answer broad questions about Insurellm's {category}.

Documents:
{combined}

Comprehensive {category} overview:"""}
    ]
    response = completion(model=MODEL, messages=messages)
    return Document(
        page_content=f"Complete overview of Insurellm {category}:\n\n{response.choices[0].message.content}",
        metadata={"doc_type": category, "source": f"overview_{category}", "is_summary": "true"},
    )


def create_summaries(documents):
    summary_docs = []

    print("Generating per-document summaries...")
    for i, doc in enumerate(documents):
        print(f"  [{i + 1}/{len(documents)}] {doc.metadata.get('source', 'unknown')}")
        try:
            summary_docs.append(generate_document_summary(doc))
        except Exception as e:
            print(f"  Warning: Failed to summarize: {e}")

    print("Generating category summaries...")
    categories = defaultdict(list)
    for doc in documents:
        categories[doc.metadata["doc_type"]].append(doc)

    for category, cat_docs in categories.items():
        print(f"  Category: {category} ({len(cat_docs)} docs)")
        try:
            summary_docs.append(generate_category_summary(category, cat_docs))
        except Exception as e:
            print(f"  Warning: Failed to summarize category {category}: {e}")

    return text_splitter.split_documents(summary_docs)


def create_embeddings(chunks):
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
    documents = fetch_documents()
    print(f"Loaded {len(documents)} documents")

    chunks = create_chunks(documents)
    print(f"Created {len(chunks)} standard chunks")

    summary_chunks = create_summaries(documents)
    print(f"Created {len(summary_chunks)} summary chunks")

    all_chunks = chunks + summary_chunks
    print(f"Total chunks to embed: {len(all_chunks)}")

    create_embeddings(all_chunks)
    print("Ingestion complete")
