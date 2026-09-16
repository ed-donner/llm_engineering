from pathlib import Path

import ollama
from chromadb import PersistentClient


BASE_DIR = Path(__file__).resolve().parent.parent

DB_NAME = str(BASE_DIR / "vector_db")
COLLECTION_NAME = "docs"

EMBED_MODEL = "nomic-embed-text:latest"
LLM_MODEL = "gemma4:latest"

RETRIEVAL_K = 8


class Result:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


chroma = PersistentClient(path=DB_NAME)

try:
    collection = chroma.get_collection(COLLECTION_NAME)
except Exception as exc:
    raise RuntimeError(
        "Chroma database not found. "
        "Run ingest.py first."
    ) from exc


def get_embedding(text):
    response = ollama.embeddings(
        model=EMBED_MODEL,
        prompt=text,
    )

    return response["embedding"]


def fetch_context(question):
    query_embedding = get_embedding(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(RETRIEVAL_K, collection.count()),
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    return [
        Result(
            page_content=text,
            metadata=metadata or {},
        )
        for text, metadata in zip(documents, metadatas)
    ]


def make_prompt(question, history, chunks):
    context = "\n\n".join(
        f"Source: {chunk.metadata.get('source', 'Unknown')}\n"
        f"{chunk.page_content}"
        for chunk in chunks
    )

    conversation = ""

    for message in history:
        role = message.get("role", "user")
        content = message.get("content", "")

        conversation += f"{role.upper()}: {content}\n"

    return f"""
You are a knowledgeable and friendly assistant for Insurellm.

Answer the user's question using the provided knowledge-base context.

Rules:
- Use the context as the primary source of truth.
- Do not invent information.
- If the answer is not available in the context, say that you don't know.
- Give a clear and useful answer.
- Consider the previous conversation when answering follow-up questions.

Previous conversation:
{conversation}

Knowledge-base context:
{context}

Current question:
{question}
"""


def answer_question(question, history=None):
    history = history or []

    chunks = fetch_context(question)

    prompt = make_prompt(
        question,
        history,
        chunks,
    )

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    answer = response["message"]["content"]

    return answer, chunks