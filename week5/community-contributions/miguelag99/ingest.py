import ollama
from pathlib import Path
from pydantic import BaseModel, Field
from chromadb import PersistentClient
from tqdm import tqdm
from litellm import completion
from multiprocessing import Pool
from tenacity import retry, wait_exponential

# By default you need to run an Ollama server with the models that you want to use.
MODEL = "ollama/gemma4:e4b"
EMBED_MODEL = "qwen3-embedding:0.6b"
OLLAMA_SERVER_URL = "http://localhost:11434"

DB_NAME = str(Path(__file__).parent / "preprocessed_db")
KNOWLEDGE_BASE_PATH = Path(__file__).parent / "poke-knowledge-base"
AVERAGE_CHUNK_SIZE = 500
collection_name = "docs"

wait = wait_exponential(multiplier=1, min=10, max=240)

WORKERS = 1

# Data formats for ingestion and retrieval

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
    
# Helper functions

def fetch_documents():
    """A homemade version of the LangChain DirectoryLoader"""

    documents = []

    for folder in KNOWLEDGE_BASE_PATH.iterdir():
        doc_type = folder.name
        for file in folder.rglob("*.md"):
            with open(file, "r", encoding="utf-8") as f:
                documents.append({"type": doc_type, "source": file.as_posix(), "text": f.read()})

    print(f"Loaded {len(documents)} documents")
    return documents

def make_prompt(document):
    how_many = (len(document["text"]) // AVERAGE_CHUNK_SIZE) + 1
    return f"""
You take a document and you split the document into overlapping chunks for a KnowledgeBase.

The document is from a pokemon and item local database from the first generation.
The document is of type: {document["type"]}
The document has been retrieved from: {document["source"]}

A chatbot will use these chunks to answer questions about the pokemon and items.
You should divide up the document as you see fit, being sure that the entire document is returned across the chunks - don't leave anything out.
This document should probably be split into at least {how_many} chunks, but you can have more or less as appropriate, ensuring that there are individual chunks to answer specific questions.
There should be overlap between the chunks as appropriate; typically about 25% overlap or about 50 words, so you have the same text in multiple chunks for best retrieval results.

For each chunk, you should provide a headline, a summary, and the original text of the chunk.
Together your chunks should represent the entire document with overlap.

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
    response = completion(
        model=MODEL, 
        messages=messages, 
        response_format=Chunks,
        base_url=OLLAMA_SERVER_URL
    )
    reply = response.choices[0].message.content
    doc_as_chunks = Chunks.model_validate_json(reply).chunks
    print(f"Document as chunks: {doc_as_chunks}")

    return [chunk.as_result(document) for chunk in doc_as_chunks]


def create_chunks(documents):
    """
    Create chunks using a number of workers in parallel.
    If you get a rate limit error, set the WORKERS to 1.
    """
    chunks = []
    with Pool(processes=WORKERS) as pool:
        for result in tqdm(pool.imap_unordered(process_document, documents), total=len(documents)):
            chunks.extend(result)
    return chunks

def create_embeddings(chunks):
    chroma = PersistentClient(path=DB_NAME)
    ollama_client = ollama.Client(host=OLLAMA_SERVER_URL)
    if collection_name in [c.name for c in chroma.list_collections()]:
        chroma.delete_collection(collection_name)

    texts = [chunk.page_content for chunk in chunks]
    emb = ollama_client.embed(model=EMBED_MODEL, input=texts)
    # vectors = [e.embedding for e in emb] ## <---------- HERE
    vectors = emb['embeddings']

    collection = chroma.get_or_create_collection(collection_name)

    ids = [str(i) for i in range(len(chunks))]
    metas = [chunk.metadata for chunk in chunks]

    collection.add(ids=ids, embeddings=vectors, documents=texts, metadatas=metas)
    print(f"Vectorstore created with {collection.count()} documents")
    
if __name__ == "__main__":
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete")