from pathlib import Path
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from langchain_core.documents import Document


# Load environment variables
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)


# Model configuration (OpenRouter)
MODEL = "openai/gpt-4o-mini"

DB_NAME = str(Path(__file__).parent.parent / "vector_db")

RETRIEVAL_K = 8


SYSTEM_PROMPT = """
You are a clinical pharmacology assistant.

Your job is to help answer questions about drug interactions, mechanisms,
and medication safety.

Use the provided context from pharmacology documents.

Guidelines:

- If an interaction exists, explain the mechanism clearly.
- Provide clinical safety guidance when possible.
- Always rely on the retrieved context.
- If the context does not contain the answer, say the interaction is not documented.

Context:
{context}
"""


# Use local embeddings (same model used during ingestion)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# Load vector database
vectorstore = Chroma(
    persist_directory=DB_NAME,
    embedding_function=embeddings
)

retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K})


# Configure LLM via OpenRouter
llm = ChatOpenAI(
    model=MODEL,
    temperature=0,
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1"
)


def fetch_context(question: str) -> list[Document]:
    """
    Retrieve relevant documents from the vector database
    """
    return retriever.invoke(question)


def combined_question(question: str, history: list[dict] = []) -> str:
    """
    Combine prior conversation history with the current question
    to improve retrieval.
    """
    prior = "\n".join(m["content"] for m in history if m["role"] == "user")
    return prior + "\n" + question


def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Document]]:
    """
    RAG pipeline: retrieve context + generate grounded answer
    """

    combined = combined_question(question, history)

    docs = fetch_context(combined)

    context = "\n\n".join(doc.page_content for doc in docs)

    system_prompt = SYSTEM_PROMPT.format(context=context)

    messages = [SystemMessage(content=system_prompt)]

    messages.extend(convert_to_messages(history))

    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)

    return response.content, docs