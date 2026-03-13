from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from chromadb import PersistentClient
from tqdm import tqdm
from litellm import completion
from multiprocessing import Pool
from tenacity import retry, wait_exponential
from langchain_docling import DoclingLoader


load_dotenv(override=True)

MODEL = "openai/gpt-4.1-nano"

DB_NAME = str(Path(__file__).parent / "tax_db")
collection_name = "docs"
embedding_model = "text-embedding-3-large"
KNOWLEDGE_BASE_PATH = Path(__file__).parent / "knowledge-base"
AVERAGE_CHUNK_SIZE = 1000
wait = wait_exponential(multiplier=1, min=10, max=240)


WORKERS = 3

openai = OpenAI()


class Result(BaseModel):
    page_content: str
    metadata: dict


class Chunk(BaseModel):
    headline: str = Field(
        description="A specific heading for this tax provision, rule, or topic (e.g., 'VAT Exemptions', 'CIT Rate').",
    )
    summary: str = Field(
        description="A clear summary of the tax rule or obligation in this chunk, explaining the implications."
    )
    keywords: list[str] = Field(
        description="A list of important tax-related keywords found in this chunk (e.g., 'WHT', 'FIRS', 'Compliance')."
    )
    original_text: str = Field(
        description="The original text of this chunk from the document, exactly as is."
    )

    def as_result(self, document):
        metadata = {"source": document["source"], "type": document["type"]}
        return Result(
            page_content=f"Headline: {self.headline}\nKeywords: {', '.join(self.keywords)}\nSummary: {self.summary}\n\nOriginal Text:\n{self.original_text}",
            metadata=metadata,
        )


class Chunks(BaseModel):
    chunks: list[Chunk]


def fetch_documents():
    """A homemade version of the LangChain DirectoryLoader that also handles PDFs."""

    documents = []

    for folder in KNOWLEDGE_BASE_PATH.iterdir():
        doc_type = folder.name
        for file in tqdm(folder.rglob("*.pdf")):
            print(f"Loading PDF: {file}")
            loader = DoclingLoader(file.as_posix())
            pages = loader.load()
            text = "\n\n".join(p.page_content for p in pages)
            documents.append({"type": doc_type, "source": file.as_posix(), "text": text})

    print(f"Loaded {len(documents)} documents")
    return documents


def make_prompt(document):
    how_many = (len(document["text"]) // AVERAGE_CHUNK_SIZE) + 1
    return f"""
You are an expert Nigerian Tax Consultant and Legal Analyst.
You are processing a document regarding tax reform in Nigeria (covering CIT, PIT, VAT, WHT, etc.).

The document is of type: {document["type"]}
Source: {document["source"]}

Your goal is to split this document into coherent, semantically complete chunks for a RAG knowledge base.
Users will ask specific questions about tax rates, exemptions, penalties, and compliance.

Instructions:
1. Split the document into approximately {how_many} chunks.
2. Ensure each chunk captures a complete rule or provision. Do not cut off sentences or related clauses.
3. Maintain overlap between chunks (approx 20-30%) to preserve context.
4. For each chunk, provide:
   - **Headline**: A concise, descriptive title (e.g., "Company Income Tax Rate for Small Businesses").
   - **Summary**: A simplified explanation of the provision.
   - **Keywords**: Key terms for retrieval (e.g., "CIT", "FIRS", "Penalty").
   - **Original Text**: The exact text from the document.

Document Text:
{document["text"]}

Respond with the JSON of chunks.
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
    print(f"Created {len(chunks)} chunks from {len(documents)} documents")
    print(f"Average chunk length: {sum(len(chunk.page_content) for chunk in chunks) / len(chunks):.2f} characters")
    print(f"Sample chunk:\n{chunks[0].page_content[:500]}...\nMetadata: {chunks[0].metadata}")
    return chunks


def create_embeddings(chunks):
    chroma = PersistentClient(path=DB_NAME)
    if collection_name in [c.name for c in chroma.list_collections()]:
        chroma.delete_collection(collection_name)

    texts = [chunk.page_content for chunk in chunks]
    emb = openai.embeddings.create(model=embedding_model, input=texts).data
    vectors = [e.embedding for e in emb]

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
