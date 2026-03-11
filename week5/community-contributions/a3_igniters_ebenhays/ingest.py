from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from chromadb import PersistentClient
from tqdm import tqdm
from litellm import completion
from multiprocessing import Pool
from tenacity import retry, wait_exponential
import wikipediaapi
import os
import shutil

# Load environment variables
load_dotenv(override=True)
openroute_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_base_url = "https://openrouter.ai/api/v1"

if not openroute_api_key:
    raise ValueError("OPENROUTE_API_KEY is not set")
print("OpenRouter API key is set")
openai = OpenAI(base_url=openrouter_base_url, api_key=openroute_api_key)

# Initialize variables
MODEL = "openai/gpt-4.1-nano"
DB_NAME = "solar_system_db"
collection_name = "docs"
embedding_model = "text-embedding-3-large"
KNOWLEDGE_BASE_PATH = "knowledge-base"
AVERAGE_CHUNK_SIZE = 100
wait = wait_exponential(multiplier=1, min=10, max=240)
WORKERS = 3


# Download Wikipedia page
def download_wikipedia_page():
    # Initialize Wikipedia API
    wiki = wikipediaapi.Wikipedia(
        user_agent="AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        language="en",
    )

    page = wiki.page("Solar System")

    if not page.exists():
        print("Error: Could not find the Solar System Wikipedia page.")
        return

    # Create the main folder
    root_folder = KNOWLEDGE_BASE_PATH
    if os.path.exists(root_folder):
        shutil.rmtree(root_folder)
        print(f"Deleted folder: {root_folder}")
    os.makedirs(root_folder)
    print(f"Created folder: {root_folder}")

    # Process each section
    for section in tqdm(page.sections, desc="Processing sections"):
        # Clean the title for use as a filename
        filename = section.title.lower().replace(" ", "_").replace("/", "_") + ".md"
        file_path = os.path.join(root_folder, filename)
        # We only want sections with content
        if section.text.strip():
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# {section.title}\n\n")
                f.write(section.text)
            print(f"Saved: {filename}")

        # Optional: Handle sub-sections by flattening them into the same file
        for sub in section.sections:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n## {sub.title}\n\n")
                f.write(sub.text)

    print("\nKnowledge Base built successfully!")


# Define models
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
            page_content=self.headline
            + "\n\n"
            + self.summary
            + "\n\n"
            + self.original_text,
            metadata=metadata,
        )


class Chunks(BaseModel):
    chunks: list[Chunk]


def fetch_documents():
    """Fetch documents from the knowledge base"""
    documents = []
    kb_path = Path(__file__).parent / KNOWLEDGE_BASE_PATH
    if not kb_path.exists():
        print(f"Error: Knowledge base not found: {kb_path}")
        return documents

    for file in kb_path.rglob("*.md"):
        doc_type = file.stem
        with open(file, "r", encoding="utf-8") as f:
            documents.append(
                {"type": doc_type, "source": file.as_posix(), "text": f.read()}
            )

    print(f"Loaded {len(documents)} documents")
    return documents


def make_prompt(document):
    how_many = (len(document["text"]) // AVERAGE_CHUNK_SIZE) + 1
    return f"""
You take a document and you split the document into overlapping chunks for a KnowledgeBase.

The document is from the shared drive of a company called SolarFacts.
The document is of type: {document["type"]}
The document has been retrieved from: {document["source"]}

A chatbot will use these chunks to answer questions about the company.
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
        for result in tqdm(
            pool.imap_unordered(process_document, documents), total=len(documents)
        ):
            chunks.extend(result)
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


def run_ingestion():
    try:
        download_wikipedia_page()
        documents = fetch_documents()
        chunks = create_chunks(documents)
        create_embeddings(chunks)
    except Exception as e:
        print(f"An error occurred during Wikipedia page download: {e}")
        raise e
    finally:
        print("Ingestion complete")
