from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv(override=True)

# ============ LM STUDIO CONFIGURATION ============
# Model identifier loaded inside your LM Studio application
MODEL = "openai/gpt-oss-20b"
LM_STUDIO_BASE_URL = "http://127.0.0.1:1234/v1"
API_KEY = "not-needed"
# =================================================

DB_NAME = str(Path(__file__).parent.parent / "vector_db")

# HuggingFace embeddings running locally
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

RETRIEVAL_K = 17

SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant representing the company Insurellm.
You are chatting with a user about Insurellm.
If relevant, use the given context to answer any question.
If you don't know the answer, say so.
Context:
{context}
"""

# Initialize ChatOpenAI pointing to the local LM Studio /v1 endpoint
llm = ChatOpenAI(
    model=MODEL,
    base_url=LM_STUDIO_BASE_URL,
    api_key=API_KEY,
    temperature=0.0
)

# Connect to the Chroma vector store
vectorstore = Chroma(persist_directory=DB_NAME, embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K})


def fetch_context(question: str) -> list[Document]:
    """Retrieve relevant context documents for a question."""
    return retriever.invoke(question)


def combined_question(question: str, history: list[dict] = []) -> str:
    """Combine user query history into a single retrieval prompt."""
    prior = "\n".join(m["content"] for m in history if m.get("role") == "user")
    return f"{prior}\n{question}" if prior else question


def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Document]]:
    """Answer the given question with RAG; return answer and context docs."""
    combined = combined_question(question, history)
    docs = fetch_context(combined)
    context = "\n\n".join(doc.page_content for doc in docs)
    system_prompt = SYSTEM_PROMPT.format(context=context)

    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(history))
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)
    return str(response.content), docs