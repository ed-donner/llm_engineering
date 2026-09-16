# # from pathlib import Path
# # from openai import OpenAI
# # from dotenv import load_dotenv
# # from pydantic import BaseModel, Field
# # from chromadb import PersistentClient
# # from tqdm import tqdm
# # from litellm import completion
# # from multiprocessing import Pool
# # from tenacity import retry, wait_exponential


# # load_dotenv(override=True)

# # MODEL = "gemini-3.6-flash"

# # DB_NAME = str(Path(__file__).parent.parent / "preprocessed_db")
# # collection_name = "docs"
# # embedding_model = "text-embedding-3-large"
# # KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge-base"
# # AVERAGE_CHUNK_SIZE = 100
# # wait = wait_exponential(multiplier=1, min=10, max=240)


# # WORKERS = 3

# # openai = OpenAI()


# # class Result(BaseModel):
# #     page_content: str
# #     metadata: dict


# # class Chunk(BaseModel):
# #     headline: str = Field(
# #         description="A brief heading for this chunk, typically a few words, that is most likely to be surfaced in a query",
# #     )
# #     summary: str = Field(
# #         description="A few sentences summarizing the content of this chunk to answer common questions"
# #     )
# #     original_text: str = Field(
# #         description="The original text of this chunk from the provided document, exactly as is, not changed in any way"
# #     )

# #     def as_result(self, document):
# #         metadata = {"source": document["source"], "type": document["type"]}
# #         return Result(
# #             page_content=self.headline + "\n\n" + self.summary + "\n\n" + self.original_text,
# #             metadata=metadata,
# #         )


# # class Chunks(BaseModel):
# #     chunks: list[Chunk]


# # def fetch_documents():
# #     """A homemade version of the LangChain DirectoryLoader"""

# #     documents = []

# #     for folder in KNOWLEDGE_BASE_PATH.iterdir():
# #         doc_type = folder.name
# #         for file in folder.rglob("*.md"):
# #             with open(file, "r", encoding="utf-8") as f:
# #                 documents.append({"type": doc_type, "source": file.as_posix(), "text": f.read()})

# #     print(f"Loaded {len(documents)} documents")
# #     return documents


# # def make_prompt(document):
# #     how_many = (len(document["text"]) // AVERAGE_CHUNK_SIZE) + 1
# #     return f"""
# # You take a document and you split the document into overlapping chunks for a KnowledgeBase.

# # The document is from the shared drive of a company called Insurellm.
# # The document is of type: {document["type"]}
# # The document has been retrieved from: {document["source"]}

# # A chatbot will use these chunks to answer questions about the company.
# # You should divide up the document as you see fit, being sure that the entire document is returned across the chunks - don't leave anything out.
# # This document should probably be split into at least {how_many} chunks, but you can have more or less as appropriate, ensuring that there are individual chunks to answer specific questions.
# # There should be overlap between the chunks as appropriate; typically about 25% overlap or about 50 words, so you have the same text in multiple chunks for best retrieval results.

# # For each chunk, you should provide a headline, a summary, and the original text of the chunk.
# # Together your chunks should represent the entire document with overlap.

# # Here is the document:

# # {document["text"]}

# # Respond with the chunks.
# # """


# # def make_messages(document):
# #     return [
# #         {"role": "user", "content": make_prompt(document)},
# #     ]


# # @retry(wait=wait)
# # def process_document(document):
# #     messages = make_messages(document)
# #     response = completion(model=MODEL, messages=messages, response_format=Chunks)
# #     reply = response.choices[0].message.content
# #     doc_as_chunks = Chunks.model_validate_json(reply).chunks
# #     return [chunk.as_result(document) for chunk in doc_as_chunks]


# # def create_chunks(documents):
# #     """
# #     Create chunks using a number of workers in parallel.
# #     If you get a rate limit error, set the WORKERS to 1.
# #     """
# #     chunks = []
# #     with Pool(processes=WORKERS) as pool:
# #         for result in tqdm(pool.imap_unordered(process_document, documents), total=len(documents)):
# #             chunks.extend(result)
# #     return chunks


# # def create_embeddings(chunks):
# #     chroma = PersistentClient(path=DB_NAME)
# #     if collection_name in [c.name for c in chroma.list_collections()]:
# #         chroma.delete_collection(collection_name)

# #     texts = [chunk.page_content for chunk in chunks]
# #     emb = openai.embeddings.create(model=embedding_model, input=texts).data
# #     vectors = [e.embedding for e in emb]

# #     collection = chroma.get_or_create_collection(collection_name)

# #     ids = [str(i) for i in range(len(chunks))]
# #     metas = [chunk.metadata for chunk in chunks]

# #     collection.add(ids=ids, embeddings=vectors, documents=texts, metadatas=metas)
# #     print(f"Vectorstore created with {collection.count()} documents")


# # if __name__ == "__main__":
# #     documents = fetch_documents()
# #     chunks = create_chunks(documents)
# #     create_embeddings(chunks)
# #     print("Ingestion complete")


# from pathlib import Path
# from dotenv import load_dotenv
# from pydantic import BaseModel, Field
# from chromadb import PersistentClient
# from tqdm import tqdm
# from litellm import completion
# from multiprocessing import Pool
# from tenacity import retry, wait_exponential
# import ollama

# load_dotenv(override=True)

# # --- Config ---
# MODEL = "gemini/gemini-3.6-flash"  # litellm needs the "gemini/" prefix for Google's API
# EMBED_MODEL = "nomic-embed-text"    # local Ollama embedding model

# DB_NAME = str(Path(__file__).parent.parent / "preprocessed_db")
# collection_name = "docs"
# KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge-base"
# AVERAGE_CHUNK_SIZE = 100
# wait = wait_exponential(multiplier=1, min=10, max=240)
# WORKERS = 3


# class Result(BaseModel):
#     page_content: str
#     metadata: dict


# class Chunk(BaseModel):
#     headline: str = Field(
#         description="A brief heading for this chunk, typically a few words, that is most likely to be surfaced in a query",
#     )
#     summary: str = Field(
#         description="A few sentences summarizing the content of this chunk to answer common questions"
#     )
#     original_text: str = Field(
#         description="The original text of this chunk from the provided document, exactly as is, not changed in any way"
#     )

#     def as_result(self, document):
#         metadata = {"source": document["source"], "type": document["type"]}
#         return Result(
#             page_content=self.headline + "\n\n" + self.summary + "\n\n" + self.original_text,
#             metadata=metadata,
#         )


# class Chunks(BaseModel):
#     chunks: list[Chunk]


# def fetch_documents():
#     """A homemade version of the LangChain DirectoryLoader"""
#     documents = []
#     for folder in KNOWLEDGE_BASE_PATH.iterdir():
#         doc_type = folder.name
#         for file in folder.rglob("*.md"):
#             with open(file, "r", encoding="utf-8") as f:
#                 documents.append({"type": doc_type, "source": file.as_posix(), "text": f.read()})

#     print(f"Loaded {len(documents)} documents")
#     return documents


# def make_prompt(document):
#     how_many = (len(document["text"]) // AVERAGE_CHUNK_SIZE) + 1
#     return f"""
# You take a document and you split the document into overlapping chunks for a KnowledgeBase.

# The document is from the shared drive of a company called Insurellm.
# The document is of type: {document["type"]}
# The document has been retrieved from: {document["source"]}

# A chatbot will use these chunks to answer questions about the company.
# You should divide up the document as you see fit, being sure that the entire document is returned across the chunks - don't leave anything out.
# This document should probably be split into at least {how_many} chunks, but you can have more or less as appropriate, ensuring that there are individual chunks to answer specific questions.
# There should be overlap between the chunks as appropriate; typically about 25% overlap or about 50 words, so you have the same text in multiple chunks for best retrieval results.

# For each chunk, you should provide a headline, a summary, and the original text of the chunk.
# Together your chunks should represent the entire document with overlap.

# Here is the document:

# {document["text"]}

# Respond with the chunks.
# """


# def make_messages(document):
#     return [
#         {"role": "user", "content": make_prompt(document)},
#     ]


# @retry(wait=wait)
# def process_document(document):
#     messages = make_messages(document)
#     response = completion(model=MODEL, messages=messages, response_format=Chunks)
#     reply = response.choices[0].message.content
#     doc_as_chunks = Chunks.model_validate_json(reply).chunks
#     return [chunk.as_result(document) for chunk in doc_as_chunks]


# def create_chunks(documents):
#     """
#     Create chunks using a number of workers in parallel.
#     If you get a rate limit error, set WORKERS to 1.
#     """
#     chunks = []
#     with Pool(processes=WORKERS) as pool:
#         for result in tqdm(pool.imap_unordered(process_document, documents), total=len(documents)):
#             chunks.extend(result)
#     return chunks


# def get_ollama_embedding(text):
#     response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
#     return response["embedding"]


# def create_embeddings(chunks):
#     chroma = PersistentClient(path=DB_NAME)
#     if collection_name in [c.name for c in chroma.list_collections()]:
#         chroma.delete_collection(collection_name)

#     texts = [chunk.page_content for chunk in chunks]

#     print("Creating embeddings locally with Ollama...")
#     vectors = [get_ollama_embedding(text) for text in tqdm(texts)]

#     collection = chroma.get_or_create_collection(collection_name)

#     ids = [str(i) for i in range(len(chunks))]
#     metas = [chunk.metadata for chunk in chunks]

#     collection.add(ids=ids, embeddings=vectors, documents=texts, metadatas=metas)
#     print(f"Vectorstore created with {collection.count()} documents")


# if __name__ == "__main__":
#     documents = fetch_documents()
#     chunks = create_chunks(documents)
#     create_embeddings(chunks)
#     print("Ingestion complete")


from pathlib import Path
from multiprocessing import Pool

import ollama
from dotenv import load_dotenv
from litellm import completion
from pydantic import BaseModel, Field
from tenacity import retry, wait_exponential
from tqdm import tqdm

load_dotenv(override=True)

# Gemini is used only for intelligent chunking.
# Ollama is used locally for embeddings, so OpenAI embeddings are not required.
MODEL = "gemini/gemini-3.6-flash"
EMBED_MODEL = "nomic-embed-text"

BASE_DIR = Path(__file__).resolve().parent.parent
DB_NAME = str(BASE_DIR / "vector_db")
COLLECTION_NAME = "docs"
KNOWLEDGE_BASE_PATH = BASE_DIR / "knowledge-base"

# Keep this at 1 for a free API key. Increase only if you need more speed.
WORKERS = 1
AVERAGE_CHUNK_SIZE = 100
wait = wait_exponential(multiplier=1, min=10, max=60)


class Result(BaseModel):
    page_content: str
    metadata: dict


class Chunk(BaseModel):
    headline: str = Field(
        description="A short heading for this chunk."
    )
    summary: str = Field(
        description="A few sentences summarizing the chunk."
    )
    original_text: str = Field(
        description="The original text of this chunk exactly as provided."
    )

    def as_result(self, document):
        return Result(
            page_content=(
                f"{self.headline}\n\n"
                f"{self.summary}\n\n"
                f"{self.original_text}"
            ),
            metadata={
                "source": document["source"],
                "type": document["type"],
            },
        )


class Chunks(BaseModel):
    chunks: list[Chunk]


def fetch_documents():
    if not KNOWLEDGE_BASE_PATH.exists():
        raise FileNotFoundError(
            f"Knowledge base not found: {KNOWLEDGE_BASE_PATH}"
        )

    documents = []

    for folder in KNOWLEDGE_BASE_PATH.iterdir():
        if not folder.is_dir():
            continue

        doc_type = folder.name

        for file in folder.rglob("*.md"):
            text = file.read_text(encoding="utf-8")
            documents.append(
                {
                    "type": doc_type,
                    "source": file.as_posix(),
                    "text": text,
                }
            )

    print(f"Loaded {len(documents)} documents")
    return documents


def make_prompt(document):
    how_many = max(1, (len(document["text"]) // AVERAGE_CHUNK_SIZE) + 1)

    return f"""
You split a document into overlapping chunks for a company knowledge base.

Company: Insurellm
Document type: {document["type"]}
Source: {document["source"]}

The chatbot will use these chunks to answer questions.
Cover the complete document; do not omit information.
Aim for approximately {how_many} or more chunks as appropriate.
Use sensible overlap between chunks.

For every chunk return:
1. headline
2. summary
3. original_text

The original_text must be copied exactly from the document.

DOCUMENT:
{document["text"]}
"""


def make_messages(document):
    return [{"role": "user", "content": make_prompt(document)}]


@retry(wait=wait)
def process_document(document):
    response = completion(
        model=MODEL,
        messages=make_messages(document),
        response_format=Chunks,
    )

    content = response.choices[0].message.content
    parsed = Chunks.model_validate_json(content).chunks
    return [chunk.as_result(document) for chunk in parsed]


def create_chunks(documents):
    chunks = []

    if WORKERS == 1:
        for document in tqdm(documents, desc="Creating chunks"):
            chunks.extend(process_document(document))
        return chunks

    with Pool(processes=WORKERS) as pool:
        for result in tqdm(
            pool.imap_unordered(process_document, documents),
            total=len(documents),
            desc="Creating chunks",
        ):
            chunks.extend(result)

    return chunks


def get_ollama_embedding(text):
    response = ollama.embeddings(
        model=EMBED_MODEL,
        prompt=text,
    )
    return response["embedding"]


def create_embeddings(chunks):
    from chromadb import PersistentClient

    chroma = PersistentClient(path=DB_NAME)

    existing = [collection.name for collection in chroma.list_collections()]
    if COLLECTION_NAME in existing:
        chroma.delete_collection(COLLECTION_NAME)

    texts = [chunk.page_content for chunk in chunks]

    print(f"Creating {len(texts)} embeddings locally with Ollama...")
    vectors = [
        get_ollama_embedding(text)
        for text in tqdm(texts, desc="Embedding")
    ]

    collection = chroma.get_or_create_collection(COLLECTION_NAME)

    ids = [str(i) for i in range(len(chunks))]
    metadatas = [chunk.metadata for chunk in chunks]

    if texts:
        collection.add(
            ids=ids,
            embeddings=vectors,
            documents=texts,
            metadatas=metadatas,
        )

    print(f"Vectorstore created with {collection.count()} documents")
    print(f"Database: {DB_NAME}")


if __name__ == "__main__":
    documents = fetch_documents()

    if not documents:
        raise RuntimeError(
            f"No .md files found under {KNOWLEDGE_BASE_PATH}"
        )

    chunks = create_chunks(documents)
    print(f"Created {len(chunks)} chunks")

    create_embeddings(chunks)
    print("Ingestion complete")
