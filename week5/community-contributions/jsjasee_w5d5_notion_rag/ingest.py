import os
import re
import time
from pathlib import Path
import yaml

import chromadb
import frontmatter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

MAX_NOTES_TO_SYNC = 20
MARKDOWN_DIR = Path("data/notion_markdown")
CHROMA_DIR = Path("chroma_db")
COLLECTION_NAME = "notion_notes"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
BATCH_SIZE = 100


def _page_title(page):
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            return "".join(item.get("plain_text", "") for item in prop.get("title", []))
    return "Untitled"


def _page_notebook_ids(page):
    for prop in page.get("properties", {}).values():
        # print("In _page_notebook_ids for a page:", prop)
        if prop.get("type") == "relation":
            return [
                item["id"].replace("-", "")
                for item in prop.get("relation", [])
                if item.get("id")
            ]
    return []


def extract_page_meta(page):
    """Return normalized metadata for a Notion database page.

    Args:
        page: Raw Notion page object from `databases.query`.

    Returns:
        Dict with page id, title, url, last edit time, notebook page ids, and source type.
    """
    return {
        "page_id": page["id"],
        "title": _page_title(page),
        "url": page["url"],
        "last_edited_time": page["last_edited_time"],
        "notebook_page_ids": _page_notebook_ids(page),
        "source_type": "notion",
    }


def query_notion_pages(notion):
    """Query the Notes database, applying optional notebook and sync-cap filters.

    Args:
        notion: Configured `notion_client.Client` instance.

    Returns:
        List of raw Notion page objects selected for sync.
    """
    database_id = os.environ["NOTION_NOTES_DATABASE_ID"]
    notebook_filter = os.getenv("NOTEBOOK_FILTER", "").strip()
    max_notes = int(MAX_NOTES_TO_SYNC or 20)
    pages, cursor = [], None

    while True:
        response = notion.data_sources.query(
            data_source_id=database_id,
            start_cursor=cursor,
            page_size=min(max_notes - len(pages), 100) if max_notes else 100,
        )
        # print(response["results"])
        for page in response["results"]:
            # print(page)
            if notebook_filter and notebook_filter not in _page_notebook_ids(page):
                continue
            pages.append(page)
            if max_notes and len(pages) >= max_notes:
                return pages
        if not response.get("has_more"):
            return pages
        cursor = response.get("next_cursor")


def _slugify(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.strip().lower()).strip("-")
    return slug or "untitled"


def clear_markdown_dir():
    """Delete prior exported markdown files from the sync directory."""
    MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
    for path in MARKDOWN_DIR.glob("*.md"):
        path.unlink()


def write_markdown_file(meta, body_md):
    """Write one note as frontmatter plus markdown body.

    Args:
        meta: Page metadata dict from `extract_page_meta`.
        body_md: Markdown body for the note.

    Returns:
        Tuple of written file path and byte count.
    """
    notebook_ids = meta.get("notebook_page_ids", [])
    notebook = notebook_ids[0] if notebook_ids else ""
    page_id_short = meta["page_id"].replace("-", "")[
        :8
    ]  # only take first 8 characters of pageid and put in title
    filename = f"{_slugify(meta['title'])}__{page_id_short}.md"
    path = MARKDOWN_DIR / filename
    meta = {
        "page_id": meta["page_id"],
        "title": meta["title"],
        "url": meta["url"],
        "last_edited_time": meta["last_edited_time"],
        "notebook": notebook,
        "source_type": meta["source_type"],
    }

    frontmatter = (
        "---\n" + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True) + "---\n\n"
    )  # yaml helps us write the frontmatter, instead of us writing it manually previously aka like literally writing "---\npage_id: 1234\ntitle: My Note\n---\n", so if there is a : in our title, it will not mess up the frontmatter, yaml will help us add quotes around it, like "title: 'My Note: 123'" instead of when we write manually, 'title: My Note: 123', which will not allow parse_formatter to execute."

    content = frontmatter + body_md.strip() + "\n"
    path.write_text(content, encoding="utf-8")
    return path, path.stat().st_size


def parse_frontmatter(text):
    """Parse one markdown file into metadata and body text.

    Args:
        text: Raw markdown file contents including YAML frontmatter. (The part between the two --- lines is the YAML frontmatter, in the markdown file.)

    Returns:
        Dict with `meta` and `body` keys.
    """
    post = frontmatter.loads(
        text
    )  # so now you have {"metadata": {... aka the YAML frontmatter}, "content": "... aka the raw text" }
    return {"meta": dict(post.metadata), "body": post.content.strip()}


def load_markdown_dir():
    """Load all exported markdown notes from disk.

    Returns:
        List of note dicts with parsed metadata, body, and source path.
    """
    docs = []
    # sorted() is loading the files in a alphabetical order, optional
    for path in sorted(MARKDOWN_DIR.glob("*.md")):
        doc = parse_frontmatter(path.read_text(encoding="utf-8"))
        doc["meta"]["source_path"] = str(path)
        docs.append(doc)
    print(f"Loaded {len(docs)} markdown pages")
    return docs


def chunk_documents(docs):
    """Split markdown docs into searchable chunk documents.

    Args:
        docs: List of dicts from `load_markdown_dir()`.

    Returns:
        List of LangChain `Document` chunks with propagated metadata.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
    chunks = []
    for doc in docs:
        meta = doc["meta"]
        title = meta.get("title", "Untitled")
        notebook = meta.get("notebook", "")
        prefix = f"# {title}\n[notebook: {notebook}]\n\n"
        for chunk_index, body_chunk in enumerate(splitter.split_text(doc["body"])):
            chunks.append(
                Document(
                    page_content=prefix + body_chunk,
                    metadata={
                        **meta,
                        "chunk_index": chunk_index,
                    },  # we are ATTACHING the metadata to the chunks, so when we chunk it into chroma DB, the metadata is already attached to it.
                )
            )
    print(f"Created {len(chunks)} chunks from {len(docs)} pages")
    return chunks


def get_chroma_client():
    """Return the persistent Chroma client used for local note search."""
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def reset_collection(client):
    """Drop and recreate the notes collection.

    Args:
        client: Persistent Chroma client.

    Returns:
        Fresh Chroma collection handle.
    """
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return client.get_or_create_collection(COLLECTION_NAME)


def rebuild_chroma_index(chunks):
    """Rebuild the `notion_notes` collection from chunk documents.

    Args:
        chunks: LangChain `Document` chunks from `chunk_documents()`.

    Returns:
        Dict with page count, chunk count, elapsed seconds, and collection name.
    """
    client = get_chroma_client()
    reset_collection(client)
    vectorstore = Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=OpenAIEmbeddings(model=EMBEDDING_MODEL),
    )
    started_at = time.time()

    # only processing 100 chunks (BATCH_SIZE) to avoid exceeding the request size limits.
    for start in range(0, len(chunks), BATCH_SIZE):
        vectorstore.add_documents(chunks[start : start + BATCH_SIZE])
    return {
        "page_count": len({chunk.metadata["page_id"] for chunk in chunks}),
        "chunk_count": len(chunks),
        "elapsed_seconds": round(time.time() - started_at, 2),
        "collection_name": COLLECTION_NAME,
    }


def sync_notion_notes():
    """Run one full sync from Notion into local markdown files.

    Returns:
        Human-readable summary string with exported, skipped, failed, and byte totals.
    """
    from dotenv import load_dotenv
    from notion_client import Client

    from utils import convert_page_to_md, get_n2m_client

    load_dotenv()
    notion = Client(auth=os.environ["NOTION_TOKEN"])
    n2m = get_n2m_client(notion)
    pages = query_notion_pages(notion)
    clear_markdown_dir()

    exported = skipped = bytes_written = 0
    failures = []
    for page in pages:
        meta = extract_page_meta(page)
        try:
            body_md = convert_page_to_md(meta["page_id"], n2m)
            if not body_md.strip():
                skipped += 1
                continue
            _, size = write_markdown_file(meta, body_md)
            exported += 1
            bytes_written += size
        except Exception as exc:
            failures.append(f"{meta['title']} ({meta['page_id']}): {exc}")

    summary = (
        f"Exported {exported}/{len(pages)} pages | "
        f"Skipped {skipped} | Failed {len(failures)} | "
        f"Bytes written {bytes_written}"
    )
    if failures:
        return summary + "\nFailures:\n- " + "\n- ".join(failures)

    docs = load_markdown_dir()
    chunks = chunk_documents(docs)
    index_stats = rebuild_chroma_index(chunks)
    return (
        summary
        + f"\nIndexed {index_stats['chunk_count']} chunks from {index_stats['page_count']} pages"
        + f" into {index_stats['collection_name']} in {index_stats['elapsed_seconds']}s"
    )
