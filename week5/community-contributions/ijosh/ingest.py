"""
Advanced RAG ingest pipeline for Insurellm knowledge base.

Key improvements over baseline:
- LLM-based semantic chunking: each chunk has headline + summary + original text
- Fine-grained chunks (avg ~150 chars) for precise per-fact retrieval
- OpenAI text-embedding-3-large for high-quality, high-dimensional embeddings
- Parallel document processing for speed
- Overlap between chunks ensures facts aren't lost at boundaries
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
DB_NAME = str(Path(__file__).parent.parent / "week5_solution_db")
COLLECTION_NAME = "docs"
EMBEDDING_MODEL = "text-embedding-3-large"
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge-base"

# Small average chunk size → many fine-grained chunks per document
# This ensures individual facts (salaries, prices, dates) are each retrievable
AVERAGE_CHUNK_SIZE = 150
WORKERS = 3
wait = wait_exponential(multiplier=1, min=10, max=240)

openai = OpenAI()


class Result(BaseModel):
    page_content: str
    metadata: dict


class Chunk(BaseModel):
    headline: str = Field(
        description=(
            "A short heading (5-15 words) for this chunk that includes the key entity names, "
            "product names, person names, monetary values, dates, and identifiers present in this chunk. "
            "This headline is used for retrieval, so make it keyword-rich."
        )
    )
    summary: str = Field(
        description=(
            "2-4 sentences summarizing ALL key facts in this chunk with exact values: "
            "include every specific number, salary, price, percentage, date, name, "
            "contract number, and identifier mentioned in the original text."
        )
    )
    original_text: str = Field(
        description="The exact verbatim original text of this chunk - do not alter, paraphrase, or omit anything."
    )

    def as_result(self, document: dict) -> Result:
        metadata = {"source": document["source"], "type": document["type"]}
        # Combine headline + summary + original for rich, multi-layer retrieval
        page_content = (
            f"{self.headline}\n\n{self.summary}\n\n{self.original_text}"
        )
        return Result(page_content=page_content, metadata=metadata)


class Chunks(BaseModel):
    chunks: list[Chunk]


def fetch_documents() -> list[dict]:
    """Load all markdown documents from the knowledge base."""
    documents = []
    for folder in KNOWLEDGE_BASE_PATH.iterdir():
        doc_type = folder.name
        for file in folder.rglob("*.md"):
            with open(file, "r", encoding="utf-8") as f:
                documents.append(
                    {"type": doc_type, "source": file.as_posix(), "text": f.read()}
                )
    print(f"Loaded {len(documents)} documents")
    return documents


def make_prompt(document: dict) -> str:
    # Aim for very granular chunks so each specific fact is independently retrievable
    how_many = max((len(document["text"]) // AVERAGE_CHUNK_SIZE) + 1, 3)
    return f"""You are a specialist at creating knowledge base chunks for a RAG (Retrieval-Augmented Generation) system.

The document belongs to the company Insurellm.
Document type: {document["type"]}
Document source: {document["source"]}

The RAG system will answer precise factual questions. You MUST create fine-grained chunks so that each specific fact
(salary, price, date, contract number, person name, product feature, tier cost, etc.) is captured in its own chunk
and can be retrieved independently.

Requirements:
1. Create AT LEAST {how_many} chunks — more is better for granularity
2. Cover EVERY fact in the document — leave NOTHING out
3. Add ~25% overlap between adjacent chunks (repeat the last ~50 words of the previous chunk at the start of the next)
4. Each chunk's headline MUST include the specific entity names, values, and identifiers in that chunk
5. Each chunk's summary MUST repeat all specific numbers, prices, names, and dates verbatim
6. The original_text must be exactly as in the source — no paraphrasing

Document text:
{document["text"]}

Respond with all chunks covering the entire document."""


def make_messages(document: dict) -> list[dict]:
    return [{"role": "user", "content": make_prompt(document)}]


@retry(wait=wait)
def process_document(document: dict) -> list[Result]:
    """Convert one document into a list of Result chunks using an LLM."""
    messages = make_messages(document)
    response = completion(model=MODEL, messages=messages, response_format=Chunks)
    reply = response.choices[0].message.content
    doc_chunks = Chunks.model_validate_json(reply).chunks
    return [chunk.as_result(document) for chunk in doc_chunks]


def create_chunks(documents: list[dict]) -> list[Result]:
    """
    Process all documents in parallel, returning a flat list of Result chunks.
    Reduce WORKERS if you hit rate limits.
    """
    chunks = []
    with Pool(processes=WORKERS) as pool:
        for result in tqdm(
            pool.imap_unordered(process_document, documents), total=len(documents)
        ):
            chunks.extend(result)
    return chunks


def create_embeddings(chunks: list[Result]) -> None:
    """Embed all chunks with text-embedding-3-large and store in Chroma."""
    chroma = PersistentClient(path=DB_NAME)
    if COLLECTION_NAME in [c.name for c in chroma.list_collections()]:
        chroma.delete_collection(COLLECTION_NAME)

    texts = [chunk.page_content for chunk in chunks]

    # Batch to stay within the API's token limit per request
    BATCH_SIZE = 100
    all_vectors = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        emb = openai.embeddings.create(model=EMBEDDING_MODEL, input=batch).data
        all_vectors.extend([e.embedding for e in emb])

    collection = chroma.get_or_create_collection(COLLECTION_NAME)
    ids = [str(i) for i in range(len(chunks))]
    metas = [chunk.metadata for chunk in chunks]

    collection.add(ids=ids, embeddings=all_vectors, documents=texts, metadatas=metas)
    print(f"Vector store created with {collection.count()} documents")


if __name__ == "__main__":
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete")
