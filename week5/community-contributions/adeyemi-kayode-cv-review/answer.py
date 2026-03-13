"""Answer questions over the CV knowledge base (retrieve, rerank, generate)."""
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from chromadb import PersistentClient
from litellm import completion
from pydantic import BaseModel, Field
from tenacity import retry, wait_exponential

load_dotenv(override=True)

MODEL = "openai/gpt-4.1-nano"
ROOT = Path(__file__).parent
DB_NAME = str(ROOT / "cv_db")
collection_name = "resumes"
embedding_model = "text-embedding-3-large"
wait = wait_exponential(multiplier=1, min=4, max=60)

openai = OpenAI()
chroma = PersistentClient(path=DB_NAME)
collection = chroma.get_or_create_collection(collection_name)

RETRIEVAL_K = 15
FINAL_K = 8

SYSTEM_PROMPT = """You are a CV review assistant. You have access to resume excerpts from several candidates.

Relevant excerpts:
{context}

Answer the user's question using only this context. Be concise. If you don't know, say so."""


class Result(BaseModel):
    page_content: str
    metadata: dict


class RankOrder(BaseModel):
    order: list[int] = Field(description="Chunk ids from most to least relevant")


@retry(wait=wait)
def rerank(question: str, chunks: list[Result]) -> list[Result]:
    sys = "You are a re-ranker. Order the chunks by relevance to the question. Reply only with the list of chunk ids (1-based), most relevant first. Include all ids."
    user = f"Question: {question}\n\n"
    for i, c in enumerate(chunks):
        user += f"# CHUNK ID: {i + 1}\n{c.page_content}\n\n"
    user += "Reply only with the list of ranked chunk ids."
    r = completion(model=MODEL, messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}], response_format=RankOrder)
    order = RankOrder.model_validate_json(r.choices[0].message.content).order
    return [chunks[i - 1] for i in order]


def fetch_context(question: str) -> list[Result]:
    emb = openai.embeddings.create(model=embedding_model, input=[question]).data[0].embedding
    out = collection.query(query_embeddings=[emb], n_results=RETRIEVAL_K)
    chunks = [Result(page_content=d, metadata=m) for d, m in zip(out["documents"][0], out["metadatas"][0])]
    reranked = rerank(question, chunks)
    return reranked[:FINAL_K]


def make_messages(question: str, chunks: list[Result]):
    context = "\n\n".join(f"[{c.metadata.get('candidate', '?')}] {c.page_content}" for c in chunks)
    system = SYSTEM_PROMPT.format(context=context)
    return [{"role": "system", "content": system}, {"role": "user", "content": question}]


@retry(wait=wait)
def answer_question(question: str) -> str:
    chunks = fetch_context(question)
    messages = make_messages(question, chunks)
    r = completion(model=MODEL, messages=messages)
    return r.choices[0].message.content
