"""
Improved RAG pipeline for Week 5 "beat the numbers" challenge.
Uses query rewriting, larger initial retrieval, LLM rerank, and a stronger answer prompt.
Drop-in replacement for implementation.answer: same fetch_context and answer_question signatures.
Run from the week5 directory so implementation and evaluation packages resolve.
"""
import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from litellm import completion
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages

WEEK5_ROOT = Path(__file__).resolve().parent.parent.parent
for _env_dir in (WEEK5_ROOT.parent, WEEK5_ROOT, Path.cwd()):
    _env = _env_dir / ".env"
    if _env.exists():
        load_dotenv(_env, override=True)
load_dotenv(override=True)

DB_NAME = str(WEEK5_ROOT / "vector_db")
MODEL = os.getenv("RAG_MODEL", "gpt-4.1-nano")
EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-3-large")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip() or None

# Base URL for the API (e.g. OpenAI, OpenRouter). Set here or via OPENAI_API_BASE in .env.
BASE_URL = os.getenv("OPENAI_API_BASE", "").strip() or None

# If using OpenRouter base URL, OPENROUTER_API_KEY can be used instead of OPENAI_API_KEY
if BASE_URL and "openrouter" in BASE_URL.lower():
    OPENAI_API_KEY = OPENAI_API_KEY or os.getenv("OPENROUTER_API_KEY", "").strip() or None

# So LiteLLM (query rewrite, rerank) uses the same key and base as LangChain
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
else:
    import warnings
    warnings.warn(
        "OPENAI_API_KEY not set. Put OPENAI_API_KEY=sk-... in a .env file in repo root or week5.",
        UserWarning,
        stacklevel=1,
    )
if BASE_URL:
    os.environ["OPENAI_API_BASE"] = BASE_URL

RETRIEVAL_K_UNRANKED = 20
RETRIEVAL_K = 10


class RankOrder(BaseModel):
    order: list[int] = Field(
        description="The order of relevance of chunks, from most relevant to least relevant, by chunk id number"
    )


_llm_kwargs = {"temperature": 0, "model": MODEL}
_emb_kwargs = {"model": EMBEDDING_MODEL}
if OPENAI_API_KEY:
    _llm_kwargs["api_key"] = OPENAI_API_KEY
    _emb_kwargs["api_key"] = OPENAI_API_KEY
if BASE_URL:
    _llm_kwargs["base_url"] = BASE_URL
    _emb_kwargs["base_url"] = BASE_URL

embeddings = OpenAIEmbeddings(**_emb_kwargs)
vectorstore = Chroma(persist_directory=DB_NAME, embedding_function=embeddings)
llm = ChatOpenAI(**_llm_kwargs)


def _rewrite_query(question: str, history: list[dict] | None = None) -> str:
    history = history or []
    history_text = "\n".join(m.get("content", "") for m in history if m.get("role") == "user")
    message = f"""
You are in a conversation answering questions about the company Insurellm.
You are about to search a Knowledge Base to answer the user's question.

Conversation history:
{history_text or "(none)"}

Current question:
{question}

Respond only with a single, refined question to search the Knowledge Base.
Keep it short and specific so it surfaces the right content. Include key entities (names, numbers, product names) when relevant.
Respond ONLY with the search query, nothing else.
"""
    response = completion(model=MODEL, messages=[{"role": "user", "content": message}])
    return (response.choices[0].message.content or question).strip()


def _fetch_unranked(question: str) -> list[Document]:
    docs = vectorstore.similarity_search(question, k=RETRIEVAL_K_UNRANKED)
    return docs


def _rerank(question: str, chunks: list[Document]) -> list[Document]:
    if not chunks:
        return []
    if len(chunks) == 1:
        return chunks
    system_prompt = """
You are a document re-ranker. Given a question and a list of text chunks from a knowledge base,
order the chunks by relevance to the question (most relevant first).
Reply only with a JSON object with one key "order": a list of chunk IDs (1-based). Include every ID exactly once, reranked.
"""
    user_prompt = f"Question:\n{question}\n\nChunks:\n"
    for i, doc in enumerate(chunks):
        user_prompt += f"# CHUNK ID: {i + 1}:\n{doc.page_content}\n\n"
    user_prompt += "Reply only with the JSON object (e.g. {\"order\": [3, 1, 2, ...]})."
    response = completion(model=MODEL, messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ], response_format=RankOrder)
    order = RankOrder.model_validate_json(response.choices[0].message.content).order
    return [chunks[i - 1] for i in order if 1 <= i <= len(chunks)]


def fetch_context(question: str) -> list[Document]:
    """Retrieve relevant context: query rewrite -> fetch 20 -> rerank -> return top 10."""
    rewritten = _rewrite_query(question, [])
    docs = _fetch_unranked(rewritten)
    reranked = _rerank(question, docs)
    return reranked[:RETRIEVAL_K]


def combined_question(question: str, history: list[dict] | None = None) -> str:
    history = history or []
    prior = "\n".join(m.get("content", "") for m in history if m.get("role") == "user")
    return (prior + "\n" + question).strip() if prior else question


SYSTEM_PROMPT = """
You are a precise assistant for the company Insurellm. Your answers are evaluated for accuracy, completeness, and relevance.

Rules:
- Use only the context below. If the answer is not in the context, say so.
- Be accurate: match facts and numbers exactly (e.g. salaries, dates, contract values, counts).
- Be complete: include all parts of the reference answer that the question asks for.
- Be relevant: answer only what was asked; no extra detail unless it directly supports the answer.

Context (with sources):
{context}

Answer the user's question based on this context. Be concise and exact.
"""


def answer_question(question: str, history: list[dict] | None = None) -> tuple[str, list[Document]]:
    """Answer using improved RAG: rewritten query, reranked context, strict prompt."""
    combined = combined_question(question, history or [])
    docs = fetch_context(combined)
    context = "\n\n".join(
        f"From {doc.metadata.get('source', 'unknown')}:\n{doc.page_content}" for doc in docs
    )
    system_prompt = SYSTEM_PROMPT.format(context=context)
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(history or []))
    messages.append(HumanMessage(content=question))
    response = llm.invoke(messages)
    return response.content, docs
