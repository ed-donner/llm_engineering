import os
from pathlib import Path
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from langchain_core.documents import Document

from dotenv import load_dotenv


load_dotenv(override=True)

MODEL = "gpt-4.1-nano"
DB_NAME = str(Path(__file__).parent.parent / "vector_db")
openrouter_url = "https://openrouter.ai/api/v1"
api_key = os.getenv('OPENAI_API_KEY')
# embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
embeddings = OpenAIEmbeddings(model="text-embedding-3-large", base_url= openrouter_url, api_key=api_key)
RETRIEVAL_K = 10

SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant. You answer questions about a website using the provided context.
If relevant, use the given context to answer any question.
If you don't know the answer, say so.
Context:
{context}
"""

_default_vectorstore = None

llm = ChatOpenAI(temperature=0, model_name=MODEL, base_url=openrouter_url, api_key=api_key)


def _get_vectorstore():
    """Lazy-load default vectorstore for backward compatibility."""
    global _default_vectorstore
    if _default_vectorstore is None:
        _default_vectorstore = Chroma(
            persist_directory=DB_NAME, embedding_function=embeddings
        )
    return _default_vectorstore


def fetch_context(question: str, vectorstore=None) -> list[Document]:
    """
    Retrieve relevant context documents for a question.
    """
    vs = vectorstore or _get_vectorstore()
    retriever = vs.as_retriever(search_kwargs={"k": RETRIEVAL_K})
    return retriever.invoke(question)


def combined_question(question: str, history: list[dict] = []) -> str:
    """
    Combine all the user's messages into a single string.
    """
    prior = "\n".join(m["content"] for m in history if m["role"] == "user")
    return prior + "\n" + question if prior else question


def answer_question(
    question: str, history: list[dict] = [], vectorstore=None
) -> tuple[str, list[Document]]:
    """
    Answer the given question with RAG; return the answer and the context documents.
    vectorstore: optional Chroma vectorstore; if None, uses default from DB_NAME.
    """
    if vectorstore is None:
        vectorstore = _get_vectorstore()
    combined = combined_question(question, history)
    docs = fetch_context(combined, vectorstore)
    context = "\n\n".join(doc.page_content for doc in docs)
    system_prompt = SYSTEM_PROMPT.format(context=context)
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(history))
    messages.append(HumanMessage(content=question))
    response = llm.invoke(messages)
    return response.content, docs
