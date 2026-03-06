"""Ingest resumes into Chroma for CV review RAG. Run once: uv run ingest.py"""
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from chromadb import PersistentClient
from tqdm import tqdm
from litellm import completion
from tenacity import retry, wait_exponential

load_dotenv(override=True)

MODEL = "openai/gpt-4.1-nano"
ROOT = Path(__file__).parent
DB_NAME = str(ROOT / "cv_db")
RESUMES_PATH = ROOT / "resume"
collection_name = "resumes"
embedding_model = "text-embedding-3-large"
AVERAGE_CHUNK_SIZE = 150
wait = wait_exponential(multiplier=1, min=4, max=60)

openai = OpenAI()


class Result(BaseModel):
    page_content: str
    metadata: dict


class Chunk(BaseModel):
    headline: str = Field(description="Short heading for this chunk (e.g. 'Backend experience', 'Python skills')")
    summary: str = Field(description="Brief summary of this chunk for retrieval")
    original_text: str = Field(description="Original text from the CV, unchanged")

    def as_result(self, document):
        metadata = {"source": document["source"], "candidate": document["candidate"]}
        return Result(
            page_content=self.headline + "\n\n" + self.summary + "\n\n" + self.original_text,
            metadata=metadata,
        )


class Chunks(BaseModel):
    chunks: list[Chunk]


def fetch_documents():
    documents = []
    for f in RESUMES_PATH.glob("*.txt"):
        text = f.read_text(encoding="utf-8")
        candidate = f.stem
        documents.append({"type": "resume", "source": f.name, "candidate": candidate, "text": text})
    print(f"Loaded {len(documents)} resumes")
    return documents


def make_prompt(document):
    n = max(1, (len(document["text"]) // AVERAGE_CHUNK_SIZE))
    return f"""
Split this CV into chunks for a CV review knowledge base.

Candidate: {document["candidate"]}
File: {document["source"]}

A chatbot will use these chunks to answer questions about candidates (e.g. skills, experience, who to hire for X).
Split the CV into about {n} chunks. Cover the whole document. Use ~25% overlap between chunks.
For each chunk provide: headline, summary, and original_text (exact copy).

Document:

{document["text"]}

Respond with the chunks.
"""


@retry(wait=wait)
def process_document(document):
    messages = [{"role": "user", "content": make_prompt(document)}]
    response = completion(model=MODEL, messages=messages, response_format=Chunks)
    doc_as_chunks = Chunks.model_validate_json(response.choices[0].message.content).chunks
    return [c.as_result(document) for c in doc_as_chunks]


def create_chunks(documents):
    chunks = []
    for doc in tqdm(documents, desc="Chunking"):
        chunks.extend(process_document(doc))
    return chunks


def create_embeddings(chunks):
    client = PersistentClient(path=DB_NAME)
    if collection_name in [c.name for c in client.list_collections()]:
        client.delete_collection(collection_name)

    texts = [c.page_content for c in chunks]
    emb = openai.embeddings.create(model=embedding_model, input=texts).data
    vectors = [e.embedding for e in emb]
    coll = client.get_or_create_collection(collection_name)
    coll.add(
        ids=[str(i) for i in range(len(chunks))],
        embeddings=vectors,
        documents=texts,
        metadatas=[c.metadata for c in chunks],
    )
    print(f"Vectorstore: {coll.count()} chunks")


if __name__ == "__main__":
    docs = fetch_documents()
    chunks = create_chunks(docs)
    create_embeddings(chunks)
    print("Ingest complete.")
