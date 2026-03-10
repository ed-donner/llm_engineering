import os
# Avoid tokenizers fork warning when using HuggingFaceEmbeddings + Chroma
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from pathlib import Path
from dotenv import load_dotenv
import frontmatter
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

load_dotenv(override=True)

#### Embeddings: open-source (no API key) or OpenAI
# Open-source options: "all-MiniLM-L6-v2" (fast), "all-mpnet-base-v2" (better quality), "BAAI/bge-small-en-v1.5"
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
# embeddings = OpenAIEmbeddings()

#### Paths
SCRIPT_DIR = Path(__file__).resolve().parent
CHROMA_DB_PATH = str(SCRIPT_DIR / "chroma_db")  # vector DB next to this script
OBSIDIAN_VAULT_PATH = "/Users/khudgins/Projects/bronze-age-campaign"


def _metadata_for_chroma(obj: dict) -> dict:
    """Flatten frontmatter to Chroma-friendly types (str, int, float, bool)."""
    out = {}
    for k, v in obj.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            out[k] = v
        elif isinstance(v, list):
            # e.g. tags: [dnd, npc] -> "dnd, npc"
            out[k] = ", ".join(str(x) for x in v) if v else ""
        elif hasattr(v, "isoformat"):  # date/datetime
            out[k] = v.isoformat()
        else:
            out[k] = str(v)
    return out


def _strip_frontmatter_raw(text: str) -> tuple[dict, str]:
    """If text starts with ---, remove the first ---...--- block; return {}, body."""
    text = text.lstrip()
    if not text.startswith("---"):
        return {}, text
    idx = text.index("\n") + 1
    end = text.find("\n---", idx)
    if end == -1:
        return {}, text
    return {}, text[end + 4 :].lstrip()  # skip closing ---


def load_obsidian_documents(vault_path: str) -> list[Document]:
    """Load all .md files from vault, parse frontmatter, return Documents with metadata."""
    vault = Path(vault_path)
    documents = []
    for path in sorted(vault.rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        try:
            post = frontmatter.loads(text)
            meta = _metadata_for_chroma(dict(post.metadata))
            content = post.content.strip()
        except Exception:
            # Non-standard or invalid frontmatter (e.g. unhashable key in YAML)
            meta, content = _strip_frontmatter_raw(text)
            content = content.strip()
        meta["source"] = str(path)
        meta["filename"] = path.name
        documents.append(Document(page_content=content or "(no content)", metadata=meta))
    return documents


#### Load the documents (with frontmatter as metadata)
documents = load_obsidian_documents(OBSIDIAN_VAULT_PATH)

#### Split the documents
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_documents(documents)

#### Embed the chunks
vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=CHROMA_DB_PATH)
# Data is already persisted to CHROMA_DB_PATH; no .persist() needed with langchain_chroma


#### Test the vectorstore
print(f"Vectorstore contains {vectorstore._collection.count()} documents")

#### Query the vectorstore (with_score returns (Document, score) tuples; metadata from frontmatter)
query = "Who is Theron?"
results = vectorstore.similarity_search_with_score(query, k=2)
for doc, score in results:
    print(f"Score: {score}")
    print(f"Metadata: {doc.metadata}")
    print(f"Content: {doc.page_content[:200]}...")
    print("-" * 50)

query = "What is the conspiracy?"
results = vectorstore.similarity_search_with_score(query, k=2)
for doc, score in results:
    print(f"Score: {score}")
    print(f"Metadata: {doc.metadata}")
    print(f"Content: {doc.page_content[:200]}...")
    print("-" * 50)