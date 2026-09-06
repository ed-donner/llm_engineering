from pathlib import Path
from dotenv import load_dotenv
from chromadb import PersistentClient
from litellm import completion
from pydantic import BaseModel, Field
from tenacity import retry, wait_exponential
from sentence_transformers import SentenceTransformer

load_dotenv(override=True)

# ============ LOCAL LM STUDIO CONFIG ============
MODEL = "openai/gpt-oss-20b"
LM_STUDIO_CONFIG = {
    "api_base": "http://127.0.0.1:1234/v1",
    "api_key": "not-needed",
    "custom_llm_provider": "openai",
}
# ===============================================

DB_NAME = str(Path(__file__).parent.parent / "preprocessed_db")
collection_name = "docs"
wait = wait_exponential(multiplier=1, min=2, max=60)

# Local HuggingFace embedding model matching ingest.py
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

chroma = PersistentClient(path=DB_NAME)
collection = chroma.get_or_create_collection(collection_name)

RETRIEVAL_K = 20
FINAL_K = 10

SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant representing the company Insurellm.
You are chatting with a user about Insurellm.
Your answer will be evaluated for accuracy, relevance and completeness, so make sure it only answers the question and fully answers it.
If you don't know the answer, say so.
For context, here are specific extracts from the Knowledge Base that might be directly relevant to the user's question:
{context}

With this context, please answer the user's question. Be accurate, relevant and complete.
"""


class Result(BaseModel):
    page_content: str
    metadata: dict


class RankOrder(BaseModel):
    order: list[int] = Field(
        description="The 1-based index numbers of the chunks ordered from most to least relevant"
    )


@retry(wait=wait)
def rerank(question: str, chunks: list[Result]) -> list[Result]:
    if not chunks:
        return []

    system_prompt = """You are a document re-ranker.
You are provided with a question and a list of relevant chunks of text.
You must rank order the provided chunks by relevance to the question, with the most relevant chunk first.
Reply only with valid JSON containing the list of ranked chunk 1-based ids."""

    user_prompt = f"The user has asked the following question:\n\n{question}\n\nCandidate Chunks:\n"
    for index, chunk in enumerate(chunks, start=1):
        user_prompt += f"# CHUNK ID {index}:\n{chunk.page_content}\n\n"
    user_prompt += "Order all chunk IDs from most relevant to least relevant."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = completion(
            model=MODEL,
            messages=messages,
            response_format=RankOrder,
            **LM_STUDIO_CONFIG
        )
        reply = response.choices[0].message.content
        order = RankOrder.model_validate_json(reply).order

        # Sanitize order indices from local model output
        valid_order = [i for i in order if 1 <= i <= len(chunks)]
        for i in range(1, len(chunks) + 1):
            if i not in valid_order:
                valid_order.append(i)

        return [chunks[i - 1] for i in valid_order]
    except Exception as e:
        print(f"Reranking encountered an error: {e}. Falling back to default order.")
        return chunks


def make_rag_messages(question: str, history: list[dict], chunks: list[Result]) -> list[dict]:
    context = "\n\n".join(
        f"Extract from {chunk.metadata.get('source', 'Unknown')}:\n{chunk.page_content}" for chunk in chunks
    )
    system_prompt = SYSTEM_PROMPT.format(context=context)
    return (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": question}]
    )


@retry(wait=wait)
def rewrite_query(question: str, history: list[dict] = []) -> str:
    message = f"""
You are in a conversation with a user, answering questions about the company Insurellm.
You are about to look up information in a Knowledge Base to answer the user's question.

This is the history of your conversation so far with the user:
{history}

And this is the user's current question:
{question}

Respond only with a short, refined question that you will use to search the Knowledge Base.
It should be a VERY short specific question most likely to surface content. Focus on the question details.
IMPORTANT: Respond ONLY with the precise knowledgebase query, nothing else.
"""
    response = completion(
        model=MODEL,
        messages=[{"role": "system", "content": message}],
        **LM_STUDIO_CONFIG
    )
    return response.choices[0].message.content.strip()


def merge_chunks(chunks: list[Result], reranked: list[Result]) -> list[Result]:
    merged = chunks[:]
    existing = {chunk.page_content for chunk in chunks}
    for chunk in reranked:
        if chunk.page_content not in existing:
            merged.append(chunk)
            existing.add(chunk.page_content)
    return merged


def fetch_context_unranked(question: str) -> list[Result]:
    query_vector = embedding_model.encode([question]).tolist()
    results = collection.query(query_embeddings=query_vector, n_results=RETRIEVAL_K)
    chunks = []
    if results and results["documents"] and len(results["documents"]) > 0:
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            chunks.append(Result(page_content=doc, metadata=meta))
    return chunks


def fetch_context(original_question: str) -> list[Result]:
    rewritten_question = rewrite_query(original_question)
    chunks1 = fetch_context_unranked(original_question)
    chunks2 = fetch_context_unranked(rewritten_question)
    chunks = merge_chunks(chunks1, chunks2)
    reranked = rerank(original_question, chunks)
    return reranked[:FINAL_K]


@retry(wait=wait)
def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Result]]:
    chunks = fetch_context(question)
    messages = make_rag_messages(question, history, chunks)
    response = completion(
        model=MODEL,
        messages=messages,
        **LM_STUDIO_CONFIG
    )
    return response.choices[0].message.content, chunks