"""Ingestion pipeline: chunks KB docs + summaries, embeds into ChromaDB.

Run generate_summaries.py first, then: uv run ingest.py
"""

from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from chromadb import PersistentClient
from tqdm import tqdm
from litellm import completion
from multiprocessing import Pool
from tenacity import retry, wait_exponential


load_dotenv(override=True)

MODEL = "openai/gpt-4.1-nano"

WEEK5_DIR = Path(__file__).parent.parent.parent.parent / "week5"
DB_NAME = str(WEEK5_DIR / "enhanced_db")
collection_name = "docs"
embedding_model = "text-embedding-3-large"
KNOWLEDGE_BASE_PATH = WEEK5_DIR / "knowledge-base"
SUMMARIES_PATH = Path(__file__).parent / "summaries"
AVERAGE_CHUNK_SIZE = 100
wait = wait_exponential(multiplier=1, min=10, max=240)

WORKERS = 3

openai = OpenAI()


class Result(BaseModel):
    page_content: str
    metadata: dict


class Chunk(BaseModel):
    headline: str = Field(
        description="A brief heading for this chunk (a few words) optimized for search queries - include key names, numbers, and terms",
    )
    summary: str = Field(
        description="A few sentences summarizing the content of this chunk, including all important numbers, dates, names, and facts"
    )
    original_text: str = Field(
        description="The original text of this chunk from the provided document, exactly as is, not changed in any way"
    )

    def as_result(self, document):
        metadata = {"source": document["source"], "type": document["type"]}
        return Result(
            page_content=self.headline + "\n\n" + self.summary + "\n\n" + self.original_text,
            metadata=metadata,
        )


class Chunks(BaseModel):
    chunks: list[Chunk]


def fetch_documents():
    """Load KB documents and generated summaries."""
    documents = []
    for folder in KNOWLEDGE_BASE_PATH.iterdir():
        if not folder.is_dir():
            continue
        doc_type = folder.name
        for file in folder.rglob("*.md"):
            with open(file, "r", encoding="utf-8") as f:
                documents.append({"type": doc_type, "source": file.as_posix(), "text": f.read()})

    if SUMMARIES_PATH.exists():
        for file in SUMMARIES_PATH.glob("*.md"):
            with open(file, "r", encoding="utf-8") as f:
                documents.append({"type": "summary", "source": file.as_posix(), "text": f.read()})

    print(f"Loaded {len(documents)} documents (including summaries)")
    return documents


def make_prompt(document):
    how_many = max((len(document["text"]) // AVERAGE_CHUNK_SIZE) + 1, 2)
    return f"""
You take a document and split it into overlapping chunks for a Knowledge Base used by a RAG chatbot.

The document is from the shared drive of a company called Insurellm.
The document is of type: {document["type"]}
The document has been retrieved from: {document["source"]}

CRITICAL RULES for chunking:
1. NEVER drop any numbers, dollar amounts, percentages, dates, or proper names. These are the most important facts.
2. Each chunk should be self-contained enough to answer a specific question.
3. There should be about 25% overlap between adjacent chunks (~50 words).
4. The entire document must be covered - don't leave anything out.
5. For tables or lists, keep related items together in the same chunk.
6. Headlines should include the most searchable terms (names, products, dollar amounts).

This document should be split into approximately {how_many} chunks, but use more or fewer as needed to ensure each chunk answers specific questions.

For each chunk, provide:
- headline: A brief, query-friendly heading with key names/numbers (e.g., "Maxine Thompson Salary $120,000" or "Healthllm Essential Tier $8,000/month")
- summary: A few sentences with ALL important facts, numbers, and dates from the chunk
- original_text: The exact original text, unchanged

Here is the document:

{document["text"]}

Respond with the chunks.
"""


def make_messages(document):
    return [
        {"role": "user", "content": make_prompt(document)},
    ]


@retry(wait=wait)
def process_document(document):
    messages = make_messages(document)
    response = completion(model=MODEL, messages=messages, response_format=Chunks)
    reply = response.choices[0].message.content
    doc_as_chunks = Chunks.model_validate_json(reply).chunks
    return [chunk.as_result(document) for chunk in doc_as_chunks]


def create_chunks(documents):
    """LLM-chunk documents in parallel."""
    chunks = []
    with Pool(processes=WORKERS) as pool:
        for result in tqdm(pool.imap_unordered(process_document, documents), total=len(documents)):
            chunks.extend(result)
    return chunks


def create_embeddings(chunks):
    chroma = PersistentClient(path=DB_NAME)
    if collection_name in [c.name for c in chroma.list_collections()]:
        chroma.delete_collection(collection_name)

    batch_size = 100
    all_vectors = []
    for i in range(0, len(chunks), batch_size):
        batch_texts = [chunk.page_content for chunk in chunks[i:i + batch_size]]
        emb = openai.embeddings.create(model=embedding_model, input=batch_texts).data
        all_vectors.extend([e.embedding for e in emb])

    collection = chroma.get_or_create_collection(collection_name)

    ids = [str(i) for i in range(len(chunks))]
    texts = [chunk.page_content for chunk in chunks]
    metas = [chunk.metadata for chunk in chunks]

    for i in range(0, len(chunks), batch_size):
        end = min(i + batch_size, len(chunks))
        collection.add(
            ids=ids[i:end],
            embeddings=all_vectors[i:end],
            documents=texts[i:end],
            metadatas=metas[i:end],
        )

    print(f"Vectorstore created with {collection.count()} documents")


if __name__ == "__main__":
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete")
