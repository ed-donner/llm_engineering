"""Document loading utilities."""
from config import KNOWLEDGE_BASE_PATH


def fetch_documents():
    """A homemade version of the LangChain DirectoryLoader.

    Reads all .md files from the knowledge base directory tree,
    returning a list of document dicts with type, source, and text.
    """
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
