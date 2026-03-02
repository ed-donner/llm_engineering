from pathlib import Path
import argparse
import torch
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from chromadb import PersistentClient
from tqdm import tqdm
from litellm import completion
from multiprocessing import Pool
from tenacity import retry, wait_exponential
from sentence_transformers import SentenceTransformer
from chromadb.utils.batch_utils import create_batches

device = "cuda" if torch.cuda.is_available() else "cpu"
if torch.cuda.is_available():
    torch.cuda.empty_cache()
print(f'Embeddings running on {device}')

load_dotenv(override=True)

MODEL = "gemini/gemini-2.5-flash"

DB_NAME = str(Path(__file__).parent / "rst_doc_db")
DEFAULT_COLLECTION_NAME = "docs"
embedding_model = "google/embeddinggemma-300M"
AVERAGE_CHUNK_SIZE = 100
wait = wait_exponential(multiplier=1, min=10, max=240)

WORKERS = 10

class Result(BaseModel):
    page_content: str
    metadata: dict


class Chunk(BaseModel):
    headline: str = Field(
        description="A brief heading for this chunk, typically a few words, that is most likely to be surfaced in a query",
    )
    summary: str = Field(
        description="A few sentences summarizing the content of this chunk to answer common questions"
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


def fetch_documents(base_path: Path):
    documents = []

    for folder in base_path.iterdir():
        if not folder.is_dir():
            continue
        doc_type = folder.name
        for file in folder.rglob("*.rst"):
            with open(file, "r", encoding="utf-8") as f:
                documents.append({"type": doc_type, "source": file.as_posix(), "text": f.read()})

    print(f"Loaded {len(documents)} documents")
    return documents


def make_prompt(document, repo):
    how_many = (len(document["text"]) // AVERAGE_CHUNK_SIZE) + 1
    return f"""
You take a document and you split the document into overlapping chunks for a KnowledgeBase.

The document is from a documentation of a github repo named {repo}.
The document is of type: {document["type"]}
The document has been retrieved from: {document["source"]}

A chatbot will use these chunks to answer questions about the repo.
You should divide up the document as you see fit, being sure that the entire document is returned across the chunks - don't leave anything out.
This document should probably be split into at least {how_many} chunks, but you can have more or less as appropriate, ensuring that there are individual chunks to answer specific questions.
There should be overlap between the chunks as appropriate; typically about 25% overlap or about 50 words, so you have the same text in multiple chunks for best retrieval results.

For each chunk, you should provide a headline, a summary, and the original text of the chunk.
Together your chunks should represent the entire document with overlap.

Here is the document:

{document["text"]}

Respond with the chunks.
"""

def make_messages(document, repo):
    return [
        {"role": "user", "content": make_prompt(document, repo)},
    ]

@retry(wait=wait)
def process_document(args):
    document, repo = args
    messages = make_messages(document, repo)
    response = completion(model=MODEL, messages=messages, response_format=Chunks)
    reply = response.choices[0].message.content
    doc_as_chunks = Chunks.model_validate_json(reply).chunks

    return [chunk.as_result(document) for chunk in doc_as_chunks]

def create_chunks(documents, repo: str):
    """
    Create chunks using a number of workers in parallel.
    If you get a rate limit error, set the WORKERS to 1.
    """

    print(f"Started chunks creation for {len(documents)} documents")
    tasks = [(doc, repo) for doc in documents]
    chunks = []

    # Avoid multiprocessing overhead when WORKERS == 1 (better CPU/memory usage)
    if WORKERS == 1:
        for result in tqdm(map(process_document, tasks), total=len(tasks)):
            chunks.extend(result)
    else:
        with Pool(processes=WORKERS) as pool:
            for result in tqdm(pool.imap_unordered(process_document, tasks), total=len(tasks)):
                chunks.extend(result)
    return chunks

def create_embeddings(chunks, collection_name: str):
    chroma = PersistentClient(path=DB_NAME)
    if collection_name in [c.name for c in chroma.list_collections()]:
        chroma.delete_collection(collection_name)

    texts = [chunk.page_content for chunk in chunks]
    ids = [str(i) for i in range(len(chunks))]
    metas = [chunk.metadata for chunk in chunks]

    # Create embeddings using SentenceTransformer in a memory-friendly way
    model = SentenceTransformer(embedding_model, device=device)
    vectors = model.encode_document(texts, batch_size=32, show_progress_bar=True).tolist()
    collection = chroma.get_or_create_collection(collection_name)

    # Create batches to avoid errors when you have a huge collection of documents 
    batches = create_batches(api=chroma,ids=list(ids), documents=list(texts), embeddings=list(vectors), metadatas=list(metas))
    for batch in batches:
        print(f"Adding batch of size {len(batch[0])}")
        collection.add(ids=batch[0], embeddings=batch[1],  documents=batch[3], metadatas=batch[2])

    # Proactively free model memory, especially important on GPU
    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print(f"Vectorstore created with {collection.count()} documents")


def ingest(repo: str) -> None:
    """
    High-level helper to run the full ingestion pipeline.

    Parameters
    ----------
    repo:
        Path (string) to the local documentation root for the repo.
        This folder should contain subfolders (doc types) with .rst files.
    """
    base_path = Path(repo).expanduser().resolve()
    documents = fetch_documents(base_path)
    chunks = create_chunks(documents, repo)

    # Use the last part of the documentation path as the collection name
    collection_name = base_path.name or DEFAULT_COLLECTION_NAME
    create_embeddings(chunks, collection_name)
    print("Ingestion complete")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest rst documentation for a downloaded GitHub repository and create a vectorstore."
        )
    )
    parser.add_argument(
        "repo",
        type=str,
        help=(
            "Path to the local documentation root for the repo. "
            "This folder should contain subfolders (doc types) with .rst files."
        ),
    )

    args = parser.parse_args()
    ingest(args.repo)


if __name__ == "__main__":
    main()
