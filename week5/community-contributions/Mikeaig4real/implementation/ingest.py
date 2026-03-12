"""
Bugs RAG ingestion: load docs, LLM-expert splitter config, chunk, embed, Chroma.
Abstracted from the Week 5 EXERCISE notebook; import and call from the notebook or scripts.
"""
from pathlib import Path
from pydantic import BaseModel, Field
from litellm import completion
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document


MD_STRUCTURE = """
Each .md file has this exact structure:
- Line 1: # Bug #<id>
- Then key-value block: **Level:**, **Description:**, **Bug Types:**, **Bug Count:**, **Tags:**, **Created:**, **Model:**
- ## Correct Code → fenced ```python ... ``` block
- ## Buggy Code → fenced ```python ... ``` block
- ## Bugs Injected → markdown table with columns # | Line | Type | Description
"""


class SplitterConfig(BaseModel):
    """LLM-expert recommended splitter type and parameters."""

    splitter_type: str = Field(
        description="Either 'recursive' (generic chunk by size/overlap) or 'markdown_header' (split by ## so each section e.g. Correct Code, Buggy Code, Bugs Injected is its own chunk with section in metadata)"
    )
    chunk_size: int = Field(
        description="For recursive: character chunk size. For markdown_header: max chunk size if we do a second pass on large sections (0 = no second pass)."
    )
    chunk_overlap: int = Field(
        description="Overlap in characters. For recursive: between chunks. For markdown_header: only used if chunk_size > 0 for second pass."
    )


def load_documents(bugs_path: Path) -> list[Document]:
    """Load all .md documents from bugs_path using LangChain DirectoryLoader."""
    loader = DirectoryLoader(
        str(bugs_path),
        glob="*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    for doc in documents:
        doc.metadata["source"] = doc.metadata.get("source", "")
    return documents


def get_splitter_config(
    documents: list[Document],
    total_chars: int,
    total_tokens: int,
    model: str,
    api_key: str,
) -> tuple[str, int, int]:
    """
    Ask LLM expert to recommend splitter_type, chunk_size, chunk_overlap.
    Returns (splitter_type, chunk_size, chunk_overlap) with splitter_type in {'markdown_header', 'recursive'}.
    """
    doc_count = len(documents)
    doc_sizes = [len(d.page_content) for d in documents]
    min_doc_chars, max_doc_chars = min(doc_sizes), max(doc_sizes)
    expert_prompt = f"""Our corpus is {doc_count} markdown documents (bugs).{MD_STRUCTURE}
Total characters: {total_chars:,}. Total tokens: {total_tokens:,}. Doc sizes range from {min_doc_chars:,} to {max_doc_chars:,} chars.

We can use one of two splitters:
1) RecursiveCharacterTextSplitter: splits by paragraph/line with chunk_size and chunk_overlap. Good generic choice.
2) MarkdownHeaderTextSplitter: splits by ## headers so "Correct Code", "Buggy Code", "Bugs Injected" become separate chunks with section name in metadata—better for RAG questions like "where is the buggy code" or "which line has the NameError".

Recommend which splitter_type to use and chunk_size/chunk_overlap. For markdown_header use chunk_size=0 (no second pass) unless sections are too large."""

    resp = completion(
        model=model,
        messages=[{"role": "user", "content": expert_prompt}],
        response_format=SplitterConfig,
        api_key=api_key,
    )
    config = SplitterConfig.model_validate_json(resp.choices[0].message.content)
    st = config.splitter_type.strip().lower()
    if "markdown" in st or "header" in st:
        splitter_type = "markdown_header"
    else:
        splitter_type = "recursive"
    return splitter_type, config.chunk_size, config.chunk_overlap


def create_chunks(
    documents: list[Document],
    splitter_type: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    """
    Split documents into chunks using markdown_header and/or recursive splitter.
    splitter_type must be 'markdown_header' or 'recursive'.
    """
    if splitter_type == "markdown_header":
        header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "Bug"), ("##", "Section")],
            strip_headers=True,
        )
        chunks = []
        for doc in documents:
            for d in header_splitter.split_text(doc.page_content):
                d.metadata.update(doc.metadata)
                chunks.append(d)
        if chunk_size > 0:
            chunk_size = max(200, min(chunk_size, 2000))
            chunk_overlap = max(0, min(chunk_overlap, chunk_size // 2))
            rec = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks = rec.split_documents(chunks)
    else:
        chunk_size = max(200, min(chunk_size, 2000))
        chunk_overlap = max(0, min(chunk_overlap, chunk_size // 2))
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        chunks = text_splitter.split_documents(documents)
    return chunks


def create_vectorstore(
    chunks: list[Document],
    db_path: Path,
    embedding_model: str,
    openai_api_base: str,
    *,
    delete_existing: bool = True,
) -> Chroma:
    """
    Embed chunks and persist to Chroma at db_path.
    Uses OpenAIEmbeddings with openai_api_base (e.g. OpenRouter). Returns the Chroma vectorstore.
    """
    embeddings = OpenAIEmbeddings(model=embedding_model, openai_api_base=openai_api_base)
    if delete_existing and db_path.exists():
        Chroma(persist_directory=str(db_path), embedding_function=embeddings).delete_collection()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(db_path),
    )
    return vectorstore
