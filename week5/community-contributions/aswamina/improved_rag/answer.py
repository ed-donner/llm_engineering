import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from litellm import completion
from pydantic import BaseModel, Field
from tenacity import retry, wait_exponential
from supabase import create_client


load_dotenv(override=True)

MODEL = "gpt-4.1-mini"
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent.parent / "knowledge-base"
SUMMARIES_PATH = Path(__file__).parent.parent / "summaries"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_INSURLLM_RAG_URL")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
collection_name = "semantic_chunked_documents"
embedding_model = "text-embedding-3-large"
wait = wait_exponential(multiplier=1, min=10, max=240)

openai = OpenAI()

RETRIEVAL_K = 40
FINAL_K = 40

question_history = []


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

    valid_ids = set(range(1, len(chunks) + 1))
    seen = set()
    safe_order = [i for i in order if i in valid_ids and not (i in seen or seen.add(i))]
    return [chunks[i - 1] for i in safe_order]


def make_rag_messages(question, history, chunks):
    context = "\n\n".join(f"Extract from {chunk.metadata['source']}:\n{chunk.page_content}" for chunk in chunks)
    system_prompt = SYSTEM_PROMPT.format(context=context)
    return [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": question}]


@retry(wait=wait)
def rewrite_query(question, history=[]):
    """Rewrite the user's question to be a more specific question that is more likely to surface relevant content in the Knowledge Base."""
    message = f"""
You are in a conversation with a user, answering questions about the company Insurellm.
You are about to look up information in a Knowledge Base to answer the user's question.

This is the history of your conversation so far with the user:
{history}

And this is the user's current question:
{question}

Rewrite specifically to expand named entities ("IIOTY winner" → "Maxine Thompson IIOTY")
Respond only with a single, refined question that you will use to search the Knowledge Base.
It should be a VERY short specific question most likely to surface content. Focus on the question details.
Don't mention the company name unless it's a general question about the company.
IMPORTANT: Respond ONLY with the knowledgebase query, nothing else.
"""
    response = completion(model=MODEL, messages=[{"role": "system", "content": message}])
    return response.choices[0].message.content


def merge_chunks(chunks, reranked):
    merged = chunks[:]
    existing = [chunk.page_content for chunk in chunks]
    for chunk in reranked:
        if chunk.page_content not in existing:
            merged.append(chunk)
    return merged



def fetch_context_unranked(question):
    query_vec = openai.embeddings.create(model=embedding_model, input=[question]).data[0].embedding  #removed , dimensions=1536
    query_str = "[" + ",".join(str(x) for x in query_vec) + "]"

    results = supabase.rpc("match_semantic_chunked_documents", {
        "query_embedding": query_str,
        "query_text": question,   # websearch_to_tsquery handles natural language better
        "match_count": RETRIEVAL_K,
    }).execute()

    return [
        Result(page_content=row["content"], metadata=row["metadata"])
        for row in results.data
    ]


def fetch_context(question):
    chunks = fetch_context_unranked(question)
    return rerank(question, chunks)


@retry(wait=wait)
def answer_question(question: str, history: list[dict] = []) -> tuple[str, list]:
    """
    Answer a question using RAG and return the answer and the retrieved context
    """
    query = rewrite_query(question, history)
    chunks = fetch_context(query)


    messages = make_rag_messages(question, history, chunks)
    response = completion(model=MODEL, messages=messages)
    return response.choices[0].message.content, chunks


