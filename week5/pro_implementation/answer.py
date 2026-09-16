# from openai import OpenAI
# from dotenv import load_dotenv
# from chromadb import PersistentClient
# from litellm import completion
# from pydantic import BaseModel, Field
# from pathlib import Path
# from tenacity import retry, wait_exponential


# load_dotenv(override=True)

# # MODEL = "openai/gpt-4.1-nano"
# MODEL = "groq/openai/gpt-oss-120b"
# DB_NAME = str(Path(__file__).parent.parent / "preprocessed_db")
# KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge-base"
# SUMMARIES_PATH = Path(__file__).parent.parent / "summaries"

# collection_name = "docs"
# embedding_model = "text-embedding-3-large"
# wait = wait_exponential(multiplier=1, min=10, max=240)

# openai = OpenAI()

# chroma = PersistentClient(path=DB_NAME)
# collection = chroma.get_or_create_collection(collection_name)

# RETRIEVAL_K = 20
# FINAL_K = 10

# SYSTEM_PROMPT = """
# You are a knowledgeable, friendly assistant representing the company Insurellm.
# You are chatting with a user about Insurellm.
# Your answer will be evaluated for accuracy, relevance and completeness, so make sure it only answers the question and fully answers it.
# If you don't know the answer, say so.
# For context, here are specific extracts from the Knowledge Base that might be directly relevant to the user's question:
# {context}

# With this context, please answer the user's question. Be accurate, relevant and complete.
# """


# class Result(BaseModel):
#     page_content: str
#     metadata: dict


# class RankOrder(BaseModel):
#     order: list[int] = Field(
#         description="The order of relevance of chunks, from most relevant to least relevant, by chunk id number"
#     )


# @retry(wait=wait)
# def rerank(question, chunks):
#     system_prompt = """
# You are a document re-ranker.
# You are provided with a question and a list of relevant chunks of text from a query of a knowledge base.
# The chunks are provided in the order they were retrieved; this should be approximately ordered by relevance, but you may be able to improve on that.
# You must rank order the provided chunks by relevance to the question, with the most relevant chunk first.
# Reply only with the list of ranked chunk ids, nothing else. Include all the chunk ids you are provided with, reranked.
# """
#     user_prompt = f"The user has asked the following question:\n\n{question}\n\nOrder all the chunks of text by relevance to the question, from most relevant to least relevant. Include all the chunk ids you are provided with, reranked.\n\n"
#     user_prompt += "Here are the chunks:\n\n"
#     for index, chunk in enumerate(chunks):
#         user_prompt += f"# CHUNK ID: {index + 1}:\n\n{chunk.page_content}\n\n"
#     user_prompt += "Reply only with the list of ranked chunk ids, nothing else."
#     messages = [
#         {"role": "system", "content": system_prompt},
#         {"role": "user", "content": user_prompt},
#     ]
#     response = completion(model=MODEL, messages=messages, response_format=RankOrder)
#     reply = response.choices[0].message.content
#     order = RankOrder.model_validate_json(reply).order
#     return [chunks[i - 1] for i in order]


# def make_rag_messages(question, history, chunks):
#     context = "\n\n".join(
#         f"Extract from {chunk.metadata['source']}:\n{chunk.page_content}" for chunk in chunks
#     )
#     system_prompt = SYSTEM_PROMPT.format(context=context)
#     return (
#         [{"role": "system", "content": system_prompt}]
#         + history
#         + [{"role": "user", "content": question}]
#     )


# @retry(wait=wait)
# def rewrite_query(question, history=[]):
#     """Rewrite the user's question to be a more specific question that is more likely to surface relevant content in the Knowledge Base."""
#     message = f"""
# You are in a conversation with a user, answering questions about the company Insurellm.
# You are about to look up information in a Knowledge Base to answer the user's question.

# This is the history of your conversation so far with the user:
# {history}

# And this is the user's current question:
# {question}

# Respond only with a short, refined question that you will use to search the Knowledge Base.
# It should be a VERY short specific question most likely to surface content. Focus on the question details.
# IMPORTANT: Respond ONLY with the precise knowledgebase query, nothing else.
# """
#     response = completion(model=MODEL, messages=[{"role": "system", "content": message}])
#     return response.choices[0].message.content


# def merge_chunks(chunks, reranked):
#     merged = chunks[:]
#     existing = [chunk.page_content for chunk in chunks]
#     for chunk in reranked:
#         if chunk.page_content not in existing:
#             merged.append(chunk)
#     return merged


# def fetch_context_unranked(question):
#     query = openai.embeddings.create(model=embedding_model, input=[question]).data[0].embedding
#     results = collection.query(query_embeddings=[query], n_results=RETRIEVAL_K)
#     chunks = []
#     for result in zip(results["documents"][0], results["metadatas"][0]):
#         chunks.append(Result(page_content=result[0], metadata=result[1]))
#     return chunks


# def fetch_context(original_question):
#     rewritten_question = rewrite_query(original_question)
#     chunks1 = fetch_context_unranked(original_question)
#     chunks2 = fetch_context_unranked(rewritten_question)
#     chunks = merge_chunks(chunks1, chunks2)
#     reranked = rerank(original_question, chunks)
#     return reranked[:FINAL_K]


# @retry(wait=wait)
# def answer_question(question: str, history: list[dict] = []) -> tuple[str, list]:
#     """
#     Answer a question using RAG and return the answer and the retrieved context
#     """
#     chunks = fetch_context(question)
#     messages = make_rag_messages(question, history, chunks)
#     response = completion(model=MODEL, messages=messages)
#     return response.choices[0].message.content, chunks


from pathlib import Path

import ollama
from chromadb import PersistentClient
from dotenv import load_dotenv
from litellm import completion
from pydantic import BaseModel, Field
from tenacity import retry, wait_exponential

load_dotenv(override=True)

# Gemini handles query rewriting, reranking, and final answers.
MODEL = "gemini/gemini-3.6-flash"

# This MUST match the embedding model used by ingest.py.
EMBED_MODEL = "nomic-embed-text"

BASE_DIR = Path(__file__).resolve().parent.parent
DB_NAME = str(BASE_DIR / "vector_db")
COLLECTION_NAME = "docs"

RETRIEVAL_K = 20
FINAL_K = 10

wait = wait_exponential(multiplier=1, min=10, max=60)

SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant representing the company Insurellm.

Answer the user's question using the retrieved knowledge-base context.
Be accurate, relevant, and complete.
Do not invent facts that are not supported by the context.
If the context does not contain the answer, say that you don't know.

Retrieved context:
{context}
"""


class Result(BaseModel):
    page_content: str
    metadata: dict


class RankOrder(BaseModel):
    order: list[int] = Field(
        description=(
            "Chunk IDs ordered from most relevant to least relevant. "
            "Include every provided chunk ID exactly once."
        )
    )


chroma = PersistentClient(path=DB_NAME)

try:
    collection = chroma.get_collection(COLLECTION_NAME)
except Exception as exc:
    raise RuntimeError(
        f"Chroma collection '{COLLECTION_NAME}' was not found at "
        f"'{DB_NAME}'. Run ingest.py first."
    ) from exc


def get_ollama_embedding(text):
    response = ollama.embeddings(
        model=EMBED_MODEL,
        prompt=text,
    )
    return response["embedding"]


def fetch_context_unranked(question):
    query_embedding = get_ollama_embedding(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(RETRIEVAL_K, collection.count()),
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    return [
        Result(page_content=text, metadata=metadata or {})
        for text, metadata in zip(documents, metadatas)
    ]


@retry(wait=wait)
def rewrite_query(question, history=None):
    history = history or []

    prompt = f"""
Rewrite the user's question into one short, precise search query for
the Insurellm knowledge base.

Conversation history:
{history}

Current question:
{question}

Return ONLY the rewritten search query.
"""

    response = completion(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content.strip()


def merge_chunks(chunks):
    merged = []
    seen = set()

    for chunk in chunks:
        key = chunk.page_content
        if key not in seen:
            seen.add(key)
            merged.append(chunk)

    return merged


@retry(wait=wait)
def rerank(question, chunks):
    if not chunks:
        return []

    prompt = f"""
You are a document re-ranker.

Question:
{question}

Rank the following chunks by relevance to the question.
Most relevant first.

Return every chunk ID exactly once.

CHUNKS:
"""

    for index, chunk in enumerate(chunks, start=1):
        prompt += (
            f"\n# CHUNK ID: {index}\n"
            f"{chunk.page_content}\n"
        )

    response = completion(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format=RankOrder,
    )

    content = response.choices[0].message.content
    order = RankOrder.model_validate_json(content).order

    ranked = []

    for chunk_id in order:
        if 1 <= chunk_id <= len(chunks):
            ranked.append(chunks[chunk_id - 1])

    # If the model accidentally omitted an ID, preserve the remaining chunks.
    used = {id(chunk) for chunk in ranked}
    ranked.extend(chunk for chunk in chunks if id(chunk) not in used)

    return ranked


def fetch_context(question, history=None):
    rewritten = rewrite_query(question, history)

    original_chunks = fetch_context_unranked(question)
    rewritten_chunks = fetch_context_unranked(rewritten)

    merged = merge_chunks(original_chunks + rewritten_chunks)
    ranked = rerank(question, merged)

    return ranked[:FINAL_K]


def make_rag_messages(question, history, chunks):
    context = "\n\n".join(
        f"Source: {chunk.metadata.get('source', 'Unknown')}\n"
        f"{chunk.page_content}"
        for chunk in chunks
    )

    system_prompt = SYSTEM_PROMPT.format(context=context)

    return (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": question}]
    )


@retry(wait=wait)
def answer_question(question, history=None):
    history = history or []

    chunks = fetch_context(question, history)
    messages = make_rag_messages(question, history, chunks)

    response = completion(
        model=MODEL,
        messages=messages,
    )

    return response.choices[0].message.content, chunks
