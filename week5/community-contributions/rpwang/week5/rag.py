from pathlib import Path
import os
import re
from dataclasses import dataclass
from typing import Any
from importlib import import_module
import httpx
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage, convert_to_messages
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


load_dotenv(override=True)

OPEN_ROUTER_CHAT_MODEL = os.getenv("OPEN_ROUTER_CHAT_MODEL", "openai/gpt-4.1-nano")
OPEN_AI_CHAT_MODEL = os.getenv("OPEN_ROUTER_CHAT_MODEL", "gpt-4.1-nano")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "gemma4:e2b")

OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "qwen3-embedding:4b")
HF_EMBEDDING_MODEL = os.getenv(
    "HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

RETRIEVAL_CANDIDATES = 20
MAX_RETRIES = 3
RETRIEVAL_K = 10

BUDGETS = {
    "system": 450,
    "summary": 700,
    "rag": 2500,
    "history": 1700,
    "query": 500,
}
SUMMARY_TRIGGER = 0.8

ROOT = Path(__file__).resolve().parent
VECTOR_DB = ROOT / "vector_db"

SYSTEM_TEMPLATE = """
You are a knowledgeable and helpful assistant for Insurellm.
Use the provided context to answer precisely.
If the answer is not present in the context, say you do not know.
If the question is not relevant to Insurellm or personally identifiable information, say you cannot answer.

Rolling summary of prior conversation:
{summary}

Retrieved context:
{context}
""".strip()


@dataclass
class EvalResult:
    passing: bool
    feedback: str
    score: float


def resolve_embeddings():
    provider = os.getenv("EMBEDDING_PROVIDER")
    if not provider:
        provider = "openai" if os.getenv("OPENAI_API_KEY") else "huggingface"
    provider = provider.lower()

    if provider == "openai":
        return OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
    if provider == "ollama":
        ollama_module = import_module("langchain_ollama")
        ollama_embeddings = getattr(ollama_module, "OllamaEmbeddings")
        return ollama_embeddings(model=OLLAMA_EMBEDDING_MODEL)
    if provider == "huggingface":
        hf_module = import_module("langchain_huggingface")
        hf_embeddings = getattr(hf_module, "HuggingFaceEmbeddings")
        return hf_embeddings(model_name=HF_EMBEDDING_MODEL)
    raise ValueError("Unsupported EMBEDDING_PROVIDER. Use: openai, ollama, huggingface")


def resolve_llm():
    provider = os.getenv("LLM_PROVIDER")
    if not provider:
        provider = "openrouter" if os.getenv("OPEN_ROUTER_API_KEY") else "ollama"
    provider = provider.lower()

    if provider == "openai":
        return ChatOpenAI(model=OPEN_AI_CHAT_MODEL, temperature=0)
    if provider == "openrouter":
        OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
        # Create an httpx client that does not verify SSL certificates (for local testing with self-signed certs)
        # Create CA bundle for production use with proper certs and remove the verify=False option
        return ChatOpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPEN_ROUTER_API_KEY, model=OPEN_ROUTER_CHAT_MODEL, temperature=0, max_retries=2, http_client=httpx.Client(verify=False),)
    # Run local hosted LLM, requires Ollama running with the model pulled
    if provider == "ollama":
        ollama_module = import_module("langchain_ollama")
        chat_ollama = getattr(ollama_module, "ChatOllama")
        return chat_ollama(model=OLLAMA_CHAT_MODEL, temperature=0)
    raise ValueError("Unsupported LLM_PROVIDER. Use: openai, ollama")


embeddings = resolve_embeddings()
llm = resolve_llm()
vectorstore = Chroma(persist_directory=VECTOR_DB, embedding_function=embeddings)
retriever = vectorstore.as_retriever()

def fetch_context(question: str) -> list[Document]:
    """
    Retrieve relevant context documents for a question.
    """
    return retriever.invoke(question, k=RETRIEVAL_K)

def to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def clamp_text(text: str, token_budget: int) -> str:
    if estimate_tokens(text) <= token_budget:
        return text
    approx_chars = token_budget * 4
    return text[:approx_chars]


def history_to_text(history: list[dict]) -> str:
    return "\n".join(f"{msg['role']}: {msg['content']}" for msg in history)


def ensure_vectorstore() -> Chroma:
    if not VECTOR_DB.exists() or not any(VECTOR_DB.iterdir()):
        from ingest import ingest_knowledge_base

        ingest_knowledge_base()
    return Chroma(persist_directory=str(VECTOR_DB), embedding_function=embeddings)


def budget_aware_retrieval(question: str, token_budget: int) -> list[Document]:
    vectorstore = ensure_vectorstore()
    candidates = vectorstore.similarity_search(question, k=RETRIEVAL_CANDIDATES)

    selected = []
    used_tokens = 0
    for doc in candidates:
        chunk_tokens = estimate_tokens(doc.page_content)
        if used_tokens + chunk_tokens <= token_budget:
            selected.append(doc)
            used_tokens += chunk_tokens
        if used_tokens >= token_budget:
            break
    return selected


def evaluate_response(question: str, answer: str, context: str) -> EvalResult:
    normalized_answer = answer.strip().lower()
    if not normalized_answer:
        return EvalResult(False, "Answer is empty. Re-answer directly from context.", 0.0)

    if len(answer.strip()) < 20:
        return EvalResult(False, "Answer is too brief. Add relevant details from context.", 0.2)

    fallback_markers = ["i don't know", "do not know", "cannot answer", "not sure"]
    if any(marker in normalized_answer for marker in fallback_markers):
        return EvalResult(True, "Fallback answer accepted.", 0.8)

    answer_terms = set(re.findall(r"[a-zA-Z]{4,}", answer.lower()))
    context_terms = set(re.findall(r"[a-zA-Z]{4,}", context.lower()))
    if not answer_terms:
        return EvalResult(False, "Answer lacks substantive terms. Use retrieved facts.", 0.1)

    overlap = answer_terms.intersection(context_terms)
    overlap_ratio = len(overlap) / max(1, len(answer_terms))

    question_terms = set(re.findall(r"[a-zA-Z]{4,}", question.lower()))
    topical_overlap = len(answer_terms.intersection(question_terms))

    if overlap_ratio < 0.12:
        return EvalResult(False, "Ground answer more explicitly in retrieved context.", 0.35)
    if topical_overlap == 0:
        return EvalResult(False, "Answer does not address the user question directly.", 0.45)

    score = min(1.0, 0.6 + overlap_ratio)
    return EvalResult(True, "Pass", score)


def merge_docs(existing: list[Document], additional: list[Document]) -> list[Document]:
    merged = existing[:]
    seen = {(doc.metadata.get("source"), doc.page_content[:120]) for doc in merged}
    for doc in additional:
        key = (doc.metadata.get("source"), doc.page_content[:120])
        if key not in seen:
            merged.append(doc)
            seen.add(key)
    return merged


def patch_context(base_query: str, docs: list[Document], feedback: str, token_budget: int) -> list[Document]:
    patch_query = clamp_text(f"{base_query}\n{feedback}", BUDGETS["query"])
    extra = budget_aware_retrieval(patch_query, token_budget)
    merged = merge_docs(docs, extra)

    selected = []
    used_tokens = 0
    for doc in merged:
        doc_tokens = estimate_tokens(doc.page_content)
        if used_tokens + doc_tokens <= token_budget:
            selected.append(doc)
            used_tokens += doc_tokens
    return selected


def update_rolling_summary(summary: str, history: list[dict]) -> tuple[str, list[dict]]:
    history_text = history_to_text(history)
    if estimate_tokens(history_text) <= int(BUDGETS["history"] * SUMMARY_TRIGGER):
        return summary, history

    cutoff = max(1, len(history) // 2)
    to_compress = history[:cutoff]
    recent = history[cutoff:]
    compress_prompt = f"""
Existing summary:
{summary or "(none)"}

Conversation turns to compress:
{history_to_text(to_compress)}

Create a single concise rolling summary that preserves user intent, facts, constraints,
and open questions. Keep it under 220 tokens.
""".strip()

    response = llm.invoke(
        [
            SystemMessage(content="You summarize conversation memory."),
            HumanMessage(content=compress_prompt),
        ]
    )
    new_summary = clamp_text(to_text(response.content), BUDGETS["summary"])
    return new_summary, recent


def answer_question(
    question: str,
    history: list[dict],
    rolling_summary: str,
) -> tuple[str, list[Document], str]:
    summary, working_history = update_rolling_summary(rolling_summary, history)
    user_history = "\n".join(m["content"] for m in working_history if m["role"] == "user")
    retrieval_query = f"{user_history}\n{question}".strip()
    retrieval_query = clamp_text(retrieval_query, BUDGETS["query"])

    docs = budget_aware_retrieval(retrieval_query, BUDGETS["rag"])
    summary = clamp_text(summary, BUDGETS["summary"])

    last_answer = "I do not know based on the current context."

    for _ in range(MAX_RETRIES):
        context = "\n\n".join(doc.page_content for doc in docs)
        context = clamp_text(context, BUDGETS["rag"])

        system_prompt = SYSTEM_TEMPLATE.format(summary=summary or "(none yet)", context=context)
        messages: list[Any] = [SystemMessage(content=system_prompt)]
        messages.extend(convert_to_messages(working_history))
        messages.append(HumanMessage(content=question))

        response = llm.invoke(messages)
        answer = to_text(response.content)
        last_answer = answer

        evaluation = evaluate_response(question, answer, context)
        if evaluation.passing:
            return answer, docs, summary

        docs = patch_context(retrieval_query, docs, evaluation.feedback, BUDGETS["rag"])

    return last_answer, docs, summary
