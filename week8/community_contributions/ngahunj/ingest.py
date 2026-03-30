"""
RAG utilities for document processing and querying.
Manual implementation without ConversationalRetrievalChain.
"""

import glob
import os
import sys

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_URL = "https://conductor.arcee.ai/v1"
MODEL = "deepseek/deepseek-r1:free"

CHROMA_PATH = "vectorstore_v1_ingest"
PDF_PATH = "knowledge_base"


def create_llm(streaming=False):
    return ChatOpenAI(
        model=MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        temperature=1,
        streaming=streaming,
    )


def create_embeddings():
    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_text_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=128,
        length_function=len,
        add_start_index=True,
    )


def get_pdf_files():
    if not os.path.exists(PDF_PATH):
        os.makedirs(PDF_PATH)
        return []
    return list(glob.glob(os.path.join(PDF_PATH, "*.pdf")))


def filter_metadata(doc):
    skip_sections = {"references", "acknowledgments", "appendix"}
    section = doc.metadata.get("section", "").lower()
    return not any(s in section for s in skip_sections)


def process_documents(documents, text_splitter):
    chunks = text_splitter.split_documents(documents)
    return [chunk for chunk in chunks if filter_metadata(chunk)]


def load_or_create_vectorstore(embeddings):
    if os.path.exists(CHROMA_PATH):
        return handle_existing_vectorstore(embeddings)
    return create_new_vectorstore(embeddings)


def handle_existing_vectorstore(embeddings):
    print("Loading existing Chroma database...")
    vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

    current_pdfs = get_pdf_files()
    if not current_pdfs:
        print("No PDF files found.")
        sys.exit(1)

    collection = vectorstore.get()

    processed_files = {
        meta.get("source")
        for meta in collection["metadatas"]
        if meta and meta.get("source")
    }

    new_pdfs = [pdf for pdf in current_pdfs if pdf not in processed_files]

    if new_pdfs:
        update_vectorstore(vectorstore, new_pdfs, processed_files)
    else:
        print("No new PDFs detected.")

    return vectorstore


def update_vectorstore(vectorstore, new_pdfs, processed_files):
    print(f"Processing {len(new_pdfs)} new PDFs...")

    loader = DirectoryLoader(PDF_PATH, glob="**/*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()

    new_documents = [
        doc for doc in documents if doc.metadata.get("source") not in processed_files
    ]

    filtered_chunks = process_documents(new_documents, get_text_splitter())

    if filtered_chunks:
        vectorstore.add_documents(filtered_chunks)
        print("Vectorstore updated.")


def create_new_vectorstore(embeddings):
    print("Creating new Chroma DB...")

    pdf_files = get_pdf_files()

    if not pdf_files:
        print("No PDFs found.")
        sys.exit(1)

    loader = DirectoryLoader(PDF_PATH, glob="**/*.pdf", loader_cls=PyPDFLoader)

    documents = loader.load()

    filtered_chunks = process_documents(documents, get_text_splitter())

    return Chroma.from_documents(
        documents=filtered_chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
    )


def create_retriever(vectorstore):
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3},
    )


def format_chat_history(chat_history):
    if not chat_history:
        return ""

    history = []

    for user, assistant in chat_history:
        history.append(f"User: {user}")
        history.append(f"Assistant: {assistant}")

    return "\n".join(history)


def truncate_history(chat_history, max_turns=5):
    return chat_history[-max_turns:]


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def rag_pipeline(llm, retriever, query, chat_history):
    chat_history = truncate_history(chat_history)

    docs = retriever.invoke(query)

    context = format_docs(docs)

    history_text = format_chat_history(chat_history)

    prompt_template = ChatPromptTemplate.from_template(
        """
            You are a helpful assistant.

            Use the conversation history and context to answer the question.

            Conversation History:
            {chat_history}

            Context:
            {context}

            Question:
            {question}

            Rules:
            - Use context if relevant
            - If the answer is unknown say you don't know
            - Do not hallucinate

            Answer:
            """
    )

    prompt = prompt_template.format(
        context=context,
        chat_history=history_text,
        question=query,
    )

    response = llm.invoke(prompt)

    return {
        "answer": response.content,
        "source_documents": docs,
    }
