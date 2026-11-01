import hashlib
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

CONTRIBUTION_PATH = Path(__file__).resolve().parent
WEEK5_PATH = CONTRIBUTION_PATH.parents[1]
DB_NAME = str(CONTRIBUTION_PATH / "preprocessed_db")
collection_name = "docs"
embedding_model = "text-embedding-3-large"
KNOWLEDGE_BASE_PATH = WEEK5_PATH / "knowledge-base"
AVERAGE_CHUNK_SIZE = 100
HIERARCHY_GROUP_SIZE = 8
wait = wait_exponential(multiplier=1, min=10, max=240)


WORKERS = 3

openai = OpenAI()


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


class HierarchySummary(BaseModel):
    headline: str = Field(description="A short heading describing this group of child nodes")
    summary: str = Field(
        description="A factual routing summary that preserves important names, numbers, dates, conditions, and exceptions"
    )
    key_topics: list[str] = Field(description="Important topics and search terms in the child nodes")
    likely_questions: list[str] = Field(
        description="Questions that the information in the child nodes can answer"
    )

    def as_result(self, document, metadata):
        topics = ", ".join(self.key_topics)
        questions = "\n".join(f"- {question}" for question in self.likely_questions)
        return Result(
            page_content=(
                f"{self.headline}\n\n{self.summary}\n\n"
                f"Key topics: {topics}\n\nQuestions this content can answer:\n{questions}"
            ),
            metadata={"source": document["source"], "type": document["type"], **metadata},
        )


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
def summarize_group(document, children, level, group_index):
    child_text = "\n\n".join(
        f"# CHILD NODE {index + 1}\n{child.page_content}" for index, child in enumerate(children)
    )
    prompt = f"""
You create hierarchical routing summaries for the Insurellm Knowledge Base.

Summarize the child nodes below into one parent node. The parent will be embedded and used to decide whether a search should descend into these children.

Requirements:
- Accurately represent all major subjects in the children.
- Preserve important names, numbers, dates, conditions, exclusions, and exceptions.
- Include terminology and synonyms that a user may search for.
- State useful questions that these children can answer.
- Do not invent information or replace specific facts with vague language.
- Keep the summary concise enough for semantic retrieval.

Source: {document["source"]}
Hierarchy level: {level}

{child_text}
"""
    response = completion(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format=HierarchySummary,
    )
    reply = response.choices[0].message.content
    summary = HierarchySummary.model_validate_json(reply)
    node_id = make_node_id(document["source"], "summary", level, group_index)
    return summary.as_result(
        document,
        {
            "node_id": node_id,
            "document_id": make_document_id(document["source"]),
            "parent_id": "",
            "node_type": "summary",
            "level": level,
            "is_root": False,
        },
    )


def make_document_id(source):
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]


def make_node_id(source, node_type, level, index):
    value = f"{source}|{node_type}|{level}|{index}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def build_hierarchy(document, chunks):
    document_id = make_document_id(document["source"])
    leaves = []
    for index, chunk in enumerate(chunks):
        leaf = chunk.as_result(document)
        leaf.metadata.update(
            {
                "node_id": make_node_id(document["source"], "chunk", 0, index),
                "document_id": document_id,
                "parent_id": "",
                "node_type": "chunk",
                "level": 0,
                "is_root": False,
            }
        )
        leaves.append(leaf)

    if not leaves:
        return []

    nodes = leaves[:]
    children = leaves
    level = 1
    while children:
        parents = []
        for group_index, start in enumerate(range(0, len(children), HIERARCHY_GROUP_SIZE)):
            group = children[start : start + HIERARCHY_GROUP_SIZE]
            parent = summarize_group(document, group, level, group_index)
            for child in group:
                child.metadata["parent_id"] = parent.metadata["node_id"]
            parents.append(parent)

        nodes.extend(parents)
        if len(parents) == 1:
            parents[0].metadata["is_root"] = True
            break

        children = parents
        level += 1

    return nodes


@retry(wait=wait)
def process_document(document):
    messages = make_messages(document)
    response = completion(model=MODEL, messages=messages, response_format=Chunks)
    reply = response.choices[0].message.content
    doc_as_chunks = Chunks.model_validate_json(reply).chunks
    return build_hierarchy(document, doc_as_chunks)


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
    emb = openai.embeddings.create(model=embedding_model, input=texts).data
    vectors = [e.embedding for e in emb]

    collection = chroma.get_or_create_collection(collection_name)

    ids = [chunk.metadata["node_id"] for chunk in chunks]
    metas = [chunk.metadata for chunk in chunks]

    collection.add(ids=ids, embeddings=vectors, documents=texts, metadatas=metas)
    print(f"Vectorstore created with {collection.count()} documents")


if __name__ == "__main__":
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete")
