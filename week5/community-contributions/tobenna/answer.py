from openai import OpenAI
from dotenv import load_dotenv
from chromadb import PersistentClient
from litellm import completion
from pydantic import BaseModel, Field
from pathlib import Path
from tenacity import retry, wait_exponential


load_dotenv(override=True)

MODEL = "openai/gpt-4.1-nano"
DB_NAME = str(Path(__file__).parent / "vector_db")
COLLECTION_NAME = "pharmacy_docs"
EMBEDDING_MODEL = "text-embedding-3-large"

wait = wait_exponential(multiplier=1, min=10, max=240)

openai = OpenAI()

chroma = PersistentClient(path=DB_NAME)
collection = chroma.get_or_create_collection(COLLECTION_NAME)

RETRIEVAL_K = 20
FINAL_K = 10

SYSTEM_PROMPT = """You are PharmAssist, the friendly and knowledgeable virtual assistant for CareFirst Pharmacy.
You help customers with questions about medications, store policies, services, staff, and general health guidance.

IMPORTANT GUIDELINES:
- Be accurate, helpful, and empathetic.
- If the knowledge base contains the answer, provide it clearly and completely.
- Always recommend customers consult a CareFirst pharmacist or their doctor for personalized medical advice.
- Never diagnose conditions or recommend specific prescription medications without a doctor's involvement.
- For emergencies, advise calling 911 or going to the nearest emergency room.
- If you don't know the answer, say so honestly and suggest the customer call CareFirst at (555) 234-5678.

For context, here are relevant extracts from the CareFirst Pharmacy Knowledge Base:
{context}

Answer the customer's question using the context above. Be accurate, relevant, and complete."""


class Result(BaseModel):
    page_content: str
    metadata: dict


class RankOrder(BaseModel):
    order: list[int] = Field(
        description="The order of relevance of chunks, from most relevant to least relevant, by chunk id number"
    )


@retry(wait=wait)
def rerank(question, chunks):
    system_prompt = """You are a document re-ranker for a pharmacy customer support system.
You are provided with a customer question and a list of relevant text chunks from the pharmacy knowledge base.
The chunks are approximately ordered by relevance, but you can improve the ordering.
Rank the chunks by relevance to the question, with the most relevant chunk first.
Reply only with the list of ranked chunk ids. Include all chunk ids you are provided with, reranked."""

    user_prompt = f"Customer question:\n\n{question}\n\nRank all chunks by relevance to this question, most relevant first.\n\n"
    for index, chunk in enumerate(chunks):
        user_prompt += f"# CHUNK ID: {index + 1}:\n\n{chunk.page_content}\n\n"
    user_prompt += "Reply only with the list of ranked chunk ids."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = completion(model=MODEL, messages=messages, response_format=RankOrder)
    reply = response.choices[0].message.content
    order = RankOrder.model_validate_json(reply).order
    return [chunks[i - 1] for i in order if 1 <= i <= len(chunks)]


@retry(wait=wait)
def rewrite_query(question, history=None):
    history = history or []
    message = f"""You are the search engine for CareFirst Pharmacy's customer support system.
A customer is asking a question and you need to rewrite it into a precise search query
that will surface the most relevant content from the pharmacy knowledge base.

Conversation history:
{history}

Customer's current question:
{question}

Respond ONLY with a single, short refined search query. Focus on the key details.
Do not mention "CareFirst" unless the question is about the company itself.
IMPORTANT: Respond ONLY with the search query, nothing else."""

    response = completion(model=MODEL, messages=[{"role": "system", "content": message}])
    return response.choices[0].message.content


def fetch_context_unranked(question):
    query = openai.embeddings.create(model=EMBEDDING_MODEL, input=[question]).data[0].embedding
    results = collection.query(query_embeddings=[query], n_results=RETRIEVAL_K)
    chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append(Result(page_content=doc, metadata=meta))
    return chunks


def merge_chunks(chunks1, chunks2):
    merged = chunks1[:]
    existing = {chunk.page_content for chunk in chunks1}
    for chunk in chunks2:
        if chunk.page_content not in existing:
            merged.append(chunk)
    return merged


def fetch_context(original_question):
    rewritten_question = rewrite_query(original_question)
    chunks1 = fetch_context_unranked(original_question)
    chunks2 = fetch_context_unranked(rewritten_question)
    chunks = merge_chunks(chunks1, chunks2)
    reranked = rerank(original_question, chunks)
    return reranked[:FINAL_K]


def make_rag_messages(question, history, chunks):
    context = "\n\n".join(
        f"[Source: {chunk.metadata['source']}]\n{chunk.page_content}" for chunk in chunks
    )
    system_prompt = SYSTEM_PROMPT.format(context=context)
    return (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": question}]
    )


@retry(wait=wait)
def answer_question(question: str, history: list[dict] | None = None) -> tuple[str, list]:
    history = history or []
    chunks = fetch_context(question)
    messages = make_rag_messages(question, history, chunks)
    response = completion(model=MODEL, messages=messages)
    return response.choices[0].message.content, chunks
