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

DB_NAME = str(Path(__file__).parent / "vector_db")
COLLECTION_NAME = "pharmacy_docs"
EMBEDDING_MODEL = "text-embedding-3-large"
KNOWLEDGE_BASE_PATH = Path(__file__).parent / "knowledge-base"
AVERAGE_CHUNK_SIZE = 100

wait = wait_exponential(multiplier=1, min=10, max=240)
WORKERS = 3

openai = OpenAI()


class Result(BaseModel):
    page_content: str
    metadata: dict


class Chunk(BaseModel):
    headline: str = Field(
        description="A brief heading for this chunk (a few words) that captures the key topic — this will be used for search retrieval",
    )
    summary: str = Field(
        description="A few sentences summarizing the chunk content to answer common customer questions"
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
    documents = []
    for folder in KNOWLEDGE_BASE_PATH.iterdir():
        if not folder.is_dir():
            continue
        doc_type = folder.name
        for file in folder.rglob("*.md"):
            with open(file, "r", encoding="utf-8") as f:
                documents.append({"type": doc_type, "source": file.as_posix(), "text": f.read()})
    print(f"Loaded {len(documents)} documents")
    return documents


def make_prompt(document):
    how_many = (len(document["text"]) // AVERAGE_CHUNK_SIZE) + 1
    return f"""You take a document and split it into overlapping chunks for a Knowledge Base.

The document is from the internal knowledge base of CareFirst Pharmacy, a neighborhood pharmacy.
The document is of type: {document["type"]}
The document has been retrieved from: {document["source"]}

A customer support chatbot will use these chunks to answer questions from pharmacy customers.
Split the document as you see fit, ensuring the entire document is covered — don't leave anything out.
This document should be split into at least {how_many} chunks, but use more or fewer as appropriate, ensuring individual chunks can answer specific customer questions.
There should be overlap between chunks (about 25% overlap or ~50 words) so the same information appears in multiple chunks for better retrieval.

For each chunk, provide a headline, a summary, and the original text of the chunk.
Together your chunks should represent the entire document with overlap.

Here is the document:

{document["text"]}

Respond with the chunks."""


@retry(wait=wait)
def process_document(document):
    messages = [{"role": "user", "content": make_prompt(document)}]
    response = completion(model=MODEL, messages=messages, response_format=Chunks)
    reply = response.choices[0].message.content
    doc_as_chunks = Chunks.model_validate_json(reply).chunks
    return [chunk.as_result(document) for chunk in doc_as_chunks]


def create_chunks(documents):
    chunks = []
    with Pool(processes=WORKERS) as pool:
        for result in tqdm(pool.imap_unordered(process_document, documents), total=len(documents)):
            chunks.extend(result)
    return chunks


def create_embeddings(chunks):
    chroma = PersistentClient(path=DB_NAME)
    if COLLECTION_NAME in [c.name for c in chroma.list_collections()]:
        chroma.delete_collection(COLLECTION_NAME)

    texts = [chunk.page_content for chunk in chunks]
    emb = openai.embeddings.create(model=EMBEDDING_MODEL, input=texts).data
    vectors = [e.embedding for e in emb]

    collection = chroma.get_or_create_collection(COLLECTION_NAME)
    ids = [str(i) for i in range(len(chunks))]
    metas = [chunk.metadata for chunk in chunks]

    collection.add(ids=ids, embeddings=vectors, documents=texts, metadatas=metas)
    print(f"Vector store created with {collection.count()} documents")


if __name__ == "__main__":
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete")
