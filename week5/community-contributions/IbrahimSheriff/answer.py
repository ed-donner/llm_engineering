import logging
import os
from pathlib import Path

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from langchain_core.documents import Document
from pydantic import BaseModel, Field

from dotenv import load_dotenv

load_dotenv(override=True)

OPENROUTER_MODEL = "openai/gpt-4o-mini"
OPENAI_MODEL = "gpt-4o-mini"
DB_NAME = str(Path(__file__).parent / "vector_db")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Must match ingest: OpenRouter (openai/text-embedding-3-small) or OpenAI or HuggingFace
if OPENROUTER_API_KEY:
    embeddings = OpenAIEmbeddings(
        model="openai/text-embedding-3-small",
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
    )
else:
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

RETRIEVAL_K_PER_QUERY = 6
RERANK_TOP_K = 5
CHUNKS_FOR_RERANK = 10

SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant representing Galdunx, a digital product and creative technology studio.
You are chatting with a user about Galdunx and its services.
If relevant, use the given context to answer any question.
If you don't know the answer, say so.
Context:
{context}
"""


def _get_retriever(k: int | None = None):
    """Build retriever on each use so we see the current collection after re-ingest."""
    vs = Chroma(persist_directory=DB_NAME, embedding_function=embeddings)
    search_k = k if k is not None else RETRIEVAL_K_PER_QUERY
    return vs.as_retriever(search_kwargs={"k": search_k})

if OPENROUTER_API_KEY:
    llm = ChatOpenAI(
        temperature=0,
        model_name=OPENROUTER_MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
    )
else:
    llm = ChatOpenAI(temperature=0.5, model_name=OPENAI_MODEL)


class RankOrder(BaseModel):
    """Order of chunk ids from most to least relevant (1-based)."""
    order: list[int] = Field(
        description="The order of relevance of chunks, from most relevant to least relevant, by chunk id number",
    )


def requery_question(question: str, history: list[dict]) -> str:
    """
    Use the LLM to produce a short, retrieval-oriented query that complements the user question
    so that searching with both user and this AI query gives broader coverage.
    """
    history_text = "\n".join(
        f"{m['role']}: {m['content']}" for m in history
    ) or "(no prior messages)"
    prompt = f"""You are helping answer questions about Galdunx (a digital product and creative technology studio) using a knowledge base.

Conversation history:
{history_text}

Current user question:
{question}

Respond with a single short search query that complements the user's question and is likely to surface relevant content when used together with their question. Focus on key entities and intent. Output ONLY the search query, nothing else."""
    response = llm.invoke([HumanMessage(content=prompt)])
    return (response.content or "").strip()


def fetch_context_unranked(question: str, k: int) -> list[Document]:
    """Retrieve up to k context documents for a question (no reranking)."""
    return _get_retriever(k=k).invoke(question)


def merge_chunks(user_chunks: list[Document], ai_chunks: list[Document]) -> list[Document]:
    """Merge AI chunks into user chunks, deduplicating by page_content."""
    merged = list(user_chunks)
    existing = {doc.page_content for doc in user_chunks}
    for doc in ai_chunks:
        if doc.page_content not in existing:
            merged.append(doc)
            existing.add(doc.page_content)
    return merged


def rerank(question: str, chunks: list[Document]) -> list[Document]:
    """Reorder chunks by relevance to the question using the LLM. Returns reordered list."""
    if not chunks:
        return []
    system_prompt = """You are a document re-ranker. You are given a question and a list of text chunks from a knowledge base. Rank the chunks by relevance to the question, most relevant first. Reply only with a JSON object with one key "order": a list of chunk ids (1-based), in relevance order. Include every chunk id exactly once."""
    user_prompt = f"Question:\n\n{question}\n\nChunks:\n\n"
    for i, doc in enumerate(chunks):
        user_prompt += f"# CHUNK ID: {i + 1}:\n\n{doc.page_content}\n\n"
    user_prompt += "Reply only with the JSON object (e.g. {\"order\": [3, 1, 2, ...]})."
    structured_llm = llm.with_structured_output(RankOrder)
    result = structured_llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    return [chunks[i - 1] for i in result.order]


def fetch_context(question: str, history: list[dict]) -> list[Document]:
    """
    Requery with AI, retrieve from user + AI query, merge and dedupe, take 10, rerank, return top 5.
    """
    combined = combined_question(question, history)
    logging.info(f"Combined user question/input: {combined}")

    ai_query = requery_question(question, history)
    logging.info(f"Requery (AI search query): {ai_query}")

    user_chunks = fetch_context_unranked(combined, RETRIEVAL_K_PER_QUERY)
    ai_chunks = fetch_context_unranked(ai_query, RETRIEVAL_K_PER_QUERY)
    logging.info(f"Retrieved {len(user_chunks)} from user query, {len(ai_chunks)} from AI query.")

    merged = merge_chunks(user_chunks, ai_chunks)
    chunks_for_rerank = merged[:CHUNKS_FOR_RERANK]
    logging.info(f"Merged to {len(merged)} unique chunks, using up to {len(chunks_for_rerank)} for rerank.")

    reranked = rerank(question, chunks_for_rerank)
    docs = reranked[:RERANK_TOP_K]
    logging.info(f"Reranked, using top {len(docs)} chunks for context.")

    return docs


def combined_question(question: str, history: list[dict] = []) -> str:
    """
    Combine all the user's messages into a single string.
    """
    prior = "\n".join(m["content"] for m in history if m["role"] == "user")
    return prior + "\n" + question


def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Document]]:
    """
    Answer the given question with RAG (requery + rerank); return the answer and the context documents.
    Logs each result for debugging or tracing.
    """
    logging.basicConfig(level=logging.INFO)

    docs = fetch_context(question, history or [])
    for idx, doc in enumerate(docs):
        logging.info(f"Document {idx + 1}: {doc.page_content[:300]}")

    context = "\n\n".join(doc.page_content for doc in docs)
    logging.info(f"Context passed to system prompt: {context[:500]}")

    system_prompt = SYSTEM_PROMPT.format(context=context)
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(history or []))
    messages.append(HumanMessage(content=question))

    logging.info(f"Messages sent to LLM: {[str(getattr(m, 'content', ''))[:200] for m in messages]}")

    response = llm.invoke(messages)
    logging.info(f"LLM response: {response.content}")

    return response.content, docs
