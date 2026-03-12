"""
Multi-Agent Medical Assistant
"""

from pathlib import Path
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from agents.multi_agent_system import EnhancedMedicalAssistant

# Alias for compatibility
MultiAgentMedicalAssistant = EnhancedMedicalAssistant

# Load environment
load_dotenv(override=True)
api_key = os.getenv("OPENAI_API_KEY")

# Config
BASE_DIR = Path(__file__).parent
DB_NAME = str(BASE_DIR / "vector_db")
RETRIEVAL_K = 5  # Limit to top 5 docs for performance

# Embeddings & vectorstore
embeddings = OpenAIEmbeddings(api_key=api_key, model="text-embedding-3-large")
vectorstore = Chroma(persist_directory=DB_NAME, embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K})

# LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)


# Legacy backward-compatible functions
def fetch_context(question: str) -> list[Document]:
    """Retrieve top-k relevant documents"""
    docs = retriever.get_relevant_documents(question)
    # Truncate each doc to 1000 chars for performance
    for doc in docs:
        doc.page_content = doc.page_content[:1000]
    return docs


def combined_question(question: str, history: list[dict] = []) -> str:
    """Combine last 3 user messages + current question"""
    last_messages = [m["content"] for m in history[-3:] if m["role"] == "user"]
    return "\n".join(last_messages + [question])


def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Document]]:
    """Legacy RAG function for backward compatibility"""
    combined = combined_question(question, history)
    docs = fetch_context(combined)

    context_text = "\n\n".join(doc.page_content for doc in docs)

    system_prompt = f"""You are a clinical pharmacology assistant.

Use the following context to answer questions:

{context_text}

- Provide clear, accurate information
- If the context doesn't contain the answer, say so
- Always include medical disclaimers"""

    from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages

    # Only keep last 3 messages from history
    recent_history = history[-3:]
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(recent_history))
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)
    return response.content, docs


# Export all
__all__ = [
    "EnhancedMedicalAssistant",
    "MultiAgentMedicalAssistant",
    "vectorstore",
    "llm",
    "fetch_context",
    "combined_question",
    "answer_question",
]
