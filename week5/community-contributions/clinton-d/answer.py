from openai import OpenAI
from dotenv import load_dotenv
from chromadb import PersistentClient
from litellm import completion
from pydantic import BaseModel, Field
from pathlib import Path
from tenacity import retry, wait_exponential


load_dotenv(override=True)

MODEL = "openai/gpt-4.1-nano"
# MODEL = "groq/openai/gpt-oss-120b"
CONTRIBUTION_PATH = Path(__file__).resolve().parent
WEEK5_PATH = CONTRIBUTION_PATH.parents[1]
DB_NAME = str(CONTRIBUTION_PATH / "preprocessed_db")
KNOWLEDGE_BASE_PATH = WEEK5_PATH / "knowledge-base"
SUMMARIES_PATH = CONTRIBUTION_PATH / "summaries"

collection_name = "docs"
embedding_model = "text-embedding-3-large"
wait = wait_exponential(multiplier=1, min=10, max=240)

openai = OpenAI()

chroma = PersistentClient(path=DB_NAME)
collection = chroma.get_or_create_collection(collection_name)

RETRIEVAL_K = 20
ROOT_RETRIEVAL_K = 5
BRANCH_RETRIEVAL_K = 20
MAX_HIERARCHY_DEPTH = 10
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
        description="The order of relevance of chunks, from most relevant to least relevant, by chunk id number"
    )


class QueryVariations(BaseModel):
    questions: list[str] = Field(
        min_length=5,
        max_length=5,
        description="Five distinct variations of the user's question",
    )


@retry(wait=wait)
def rerank(question, chunks):
    system_prompt = """
You are a document re-ranker.
You are provided with a question and a list of relevant chunks of text from a query of a knowledge base.
The chunks are provided in the order they were retrieved; this should be approximately ordered by relevance, but you may be able to improve on that.
You must rank order the provided chunks by relevance to the question, with the most relevant chunk first.
Reply only with the list of ranked chunk ids, nothing else. Include all the chunk ids you are provided with, reranked.
"""
    user_prompt = f"The user has asked the following question:\n\n{question}\n\nOrder all the chunks of text by relevance to the question, from most relevant to least relevant. Include all the chunk ids you are provided with, reranked.\n\n"
    user_prompt += "Here are the chunks:\n\n"
    for index, chunk in enumerate(chunks):
        user_prompt += f"# CHUNK ID: {index + 1}:\n\n{chunk.page_content}\n\n"
    user_prompt += "Reply only with the list of ranked chunk ids, nothing else."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = completion(model=MODEL, messages=messages, response_format=RankOrder)
    reply = response.choices[0].message.content
    order = RankOrder.model_validate_json(reply).order
    return [chunks[i - 1] for i in order]


def make_rag_messages(question, history, chunks):
    context = "\n\n".join(
        f"Extract from {chunk.metadata['source']}:\n{chunk.page_content}" for chunk in chunks
    )
    system_prompt = SYSTEM_PROMPT.format(context=context)
    return (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": question}]
    )


@retry(wait=wait)
def rewrite_query(question, history=None):
    """Create five query variations likely to surface relevant Knowledge Base content."""
    if history is None:
        history = []

    message = f"""
You are in a conversation with a user.
You are about to look up information in a Knowledge Base to answer the user's question.

This is the history of your conversation so far with the user:
{history}

And this is the user's current question:
{question}

Since the conversation is contextual, understand the meaning of the user question and add details based on the history.
Create exactly five distinct, contextually-rich, short and specific variations of the question.
Vary the wording and emphasis so the questions are likely to surface complementary relevant content.

IMPORTANT: Respond with exactly five knowledge base questions.
"""
    response = completion(
        model=MODEL,
        messages=[{"role": "system", "content": message}],
        response_format=QueryVariations,
    )
    reply = response.choices[0].message.content
    return QueryVariations.model_validate_json(reply).questions


def merge_chunks(chunks, reranked):
    merged = chunks[:]
    existing = [chunk.page_content for chunk in chunks]
    for chunk in reranked:
        if chunk.page_content not in existing:
            merged.append(chunk)
    return merged


def embed_question(question):
    return openai.embeddings.create(model=embedding_model, input=[question]).data[0].embedding


def query_collection(query_embedding, n_results, where=None):
    query_args = {"query_embeddings": [query_embedding], "n_results": n_results}
    if where:
        query_args["where"] = where
    results = collection.query(**query_args)
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    return [
        Result(page_content=document, metadata=metadata)
        for document, metadata in zip(documents, metadatas)
    ]


def fetch_context_unranked(question, query_embedding=None):
    query_embedding = query_embedding or embed_question(question)
    chunks = query_collection(
        query_embedding,
        RETRIEVAL_K,
        where={"node_type": "chunk"},
    )
    if not chunks:
        # Allow retrieval from an existing flat database before hierarchical re-ingestion.
        chunks = query_collection(query_embedding, RETRIEVAL_K)
    return chunks


def fetch_context_hierarchical(question, query_embedding=None):
    query_embedding = query_embedding or embed_question(question)
    frontier = query_collection(
        query_embedding,
        ROOT_RETRIEVAL_K,
        where={"is_root": True},
    )
    chunks = []
    visited = set()

    for _ in range(MAX_HIERARCHY_DEPTH):
        parent_ids = [
            node.metadata["node_id"]
            for node in frontier
            if node.metadata.get("node_id") not in visited
        ]
        if not parent_ids:
            break

        visited.update(parent_ids)
        children = query_collection(
            query_embedding,
            BRANCH_RETRIEVAL_K,
            where={"parent_id": {"$in": parent_ids}},
        )
        frontier = []
        for child in children:
            if child.metadata.get("node_type") == "chunk":
                chunks.append(child)
            else:
                frontier.append(child)

    return chunks


def fetch_context(original_question, history=None):
    rewritten_questions = rewrite_query(original_question, history)
    print(rewritten_questions)
    chunks = []
    for question in [original_question, *rewritten_questions]:
        query_embedding = embed_question(question)
        direct_chunks = fetch_context_unranked(question, query_embedding)
        hierarchical_chunks = fetch_context_hierarchical(question, query_embedding)
        chunks = merge_chunks(chunks, direct_chunks)
        chunks = merge_chunks(chunks, hierarchical_chunks)
    reranked = rerank(original_question, chunks)
    return reranked[:FINAL_K]


@retry(wait=wait)
def answer_question(question: str, history: list[dict] = []) -> tuple[str, list]:
    """
    Answer a question using RAG and return the answer and the retrieved context
    """
    chunks = fetch_context(question, history)
    messages = make_rag_messages(question, history, chunks)
    response = completion(model=MODEL, messages=messages)
    return response.choices[0].message.content, chunks
