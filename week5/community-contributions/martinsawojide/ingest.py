from pathlib import Path
# from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from chromadb import PersistentClient
from tqdm import tqdm
from litellm import completion
from multiprocessing import Pool
from tenacity import retry, wait_exponential
from sentence_transformers import SentenceTransformer

load_dotenv(override=True)

MODEL = "openrouter/openai/gpt-oss-120b"

DB_NAME = str(Path(__file__).parent.parent / "preprocessed_db")
collection_name = "docs"
summaries_collection_name = "summaries"
embedding_model = SentenceTransformer("BAAI/bge-large-en-v1.5")
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge-base"
AVERAGE_CHUNK_SIZE = 100
wait = wait_exponential(multiplier=1, min=10, max=240)


WORKERS = 3


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
    section_title: str | None = Field(
        default=None,
        description="The section or subsection this chunk belongs to (e.g. Terms, Renewal, Features). Use markdown ##-style headings when applicable.",
    )
    section_context: str | None = Field(
        default=None,
        description="Optional 1-2 sentence description of the section's scope or what it covers.",
    )

    def as_result(self, document):
        metadata = {"source": document["source"], "type": document["type"]}
        page_content = build_enriched_content(document, self)
        return Result(page_content=page_content, metadata=metadata)


class Chunks(BaseModel):
    chunks: list[Chunk]

# Max lengths for enrichment header to avoid diluting embeddings
MAX_SOURCE_LEN = 120
MAX_SECTION_CONTEXT_LEN = 200


def get_doc_title(document: dict) -> str:
    """Derive document title from filename or first # heading in raw text."""
    text = document.get("text", "")
    if text.strip():
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("# ") and len(line) > 2:
                return line[2:].strip()
    return Path(document["source"]).stem.replace("-", " ").replace("_", " ").title()


def build_enriched_content(document: dict, chunk: Chunk) -> str:
    """Build enriched page_content with structured document/section header."""
    doc_title = get_doc_title(document)
    doc_type = document.get("type", "")
    source = (document.get("source", "") or "")[:MAX_SOURCE_LEN]
    section_title = (chunk.section_title or chunk.headline or "General").strip()
    section_context = (chunk.section_context or "").strip()[:MAX_SECTION_CONTEXT_LEN]

    lines = [
        f"[Document] {doc_title}",
        f"[Type] {doc_type}",
        f"[Source] {source}",
        f"[Section] {section_title}",
    ]
    if section_context:
        lines.append(f"[Section context] {section_context}")
    lines.append("---")
    lines.append("")
    lines.append(chunk.headline)
    lines.append("")
    lines.append(chunk.summary)
    lines.append("")
    lines.append(chunk.original_text)
    return "\n".join(lines)


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

The document is from the shared drive of a company called Insurellm.
The document is of type: {document["type"]}
The document has been retrieved from: {document["source"]}

A chatbot will use these chunks to answer questions about the company.
You should divide up the document as you see fit, being sure that the entire document is returned across the chunks - don't leave anything out.
This document should probably be split into at least {how_many} chunks, but you can have more or less as appropriate, ensuring that there are individual chunks to answer specific questions.
There should be overlap between the chunks as appropriate; typically about 25% overlap or about 50 words, so you have the same text in multiple chunks for best retrieval results.

For each chunk, you should provide: headline, summary, original text, section_title (the section or subsection, e.g. Terms, Renewal, Features - use consistent ##-style headings within the document), and optionally section_context (1-2 sentences describing what the section covers).
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
    response = completion(model=MODEL, messages=messages, response_format=Chunks)
    reply = response.choices[0].message.content
    doc_as_chunks = Chunks.model_validate_json(reply).chunks
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
    if collection_name in [c.name for c in chroma.list_collections()]:
        chroma.delete_collection(collection_name)

    texts = [chunk.page_content for chunk in chunks]
    vectors = embedding_model.encode(texts).tolist()

    collection = chroma.get_or_create_collection(collection_name)

    ids = [str(i) for i in range(len(chunks))]
    metas = [chunk.metadata for chunk in chunks]

    collection.add(ids=ids, embeddings=vectors, documents=texts, metadatas=metas)
    print(f"Vectorstore created with {collection.count()} documents")


class DocumentSummary(BaseModel):
    summary: str = Field(description="A 2-4 sentence summary of the document for a QA system.")


@retry(wait=wait)
def summarize_document(document: dict) -> str:
    """Generate a short document-level summary via LLM."""
    prompt = f"""Summarize the following document in 2-4 sentences for a QA system. Focus on what someone might ask about.

Document type: {document["type"]}
Source: {document["source"]}

{document["text"][:8000]}

Respond with only the summary."""
    response = completion(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format=DocumentSummary,
    )
    reply = response.choices[0].message.content
    return DocumentSummary.model_validate_json(reply).summary


def create_summary_index(documents: list[dict]) -> None:
    """Build a second Chroma collection of document-level summaries."""
    chroma = PersistentClient(path=DB_NAME)
    if summaries_collection_name in [c.name for c in chroma.list_collections()]:
        chroma.delete_collection(summaries_collection_name)

    summaries = []
    for i, doc in enumerate(tqdm(documents, desc="Summarizing documents")):
        summary_text = summarize_document(doc)
        title = get_doc_title(doc)
        # Store as "[Document] title\n\nsummary" so retrieval returns readable context
        page_content = f"[Document] {title}\n\n{summary_text}"
        summaries.append({
            "id": f"summary_{i}_{Path(doc['source']).stem}",
            "content": page_content,
            "metadata": {
                "source": doc["source"],
                "type": doc["type"],
                "title": title,
                "summary_type": "document",
            },
        })

    if not summaries:
        print("No summaries to index.")
        return

    texts = [s["content"] for s in summaries]
    vectors = embedding_model.encode(texts).tolist()
    ids = [s["id"] for s in summaries]
    metas = [s["metadata"] for s in summaries]
    coll = chroma.get_or_create_collection(summaries_collection_name)
    coll.add(ids=ids, embeddings=vectors, documents=texts, metadatas=metas)
    print(f"Summary index created with {coll.count()} entries.")


if __name__ == "__main__":
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    create_summary_index(documents)
    print("Ingestion complete")
