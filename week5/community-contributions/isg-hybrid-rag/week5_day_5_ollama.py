"""Advanced RAG Techniques using Reranking & Query Rewriting"""
import os
import re
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ConfigDict, AliasChoices
from chromadb import PersistentClient
from tqdm import tqdm
from litellm import completion
import numpy as np
from sklearn.manifold import TSNE
import plotly.graph_objects as go

load_dotenv(override=True)

API_KEY              = "ollama"
MODEL                = "ollama_chat/ornith:9b"
URL                  = "http://localhost:11434"
OPENAI               = OpenAI()
CLIENT               = OpenAI(api_key=API_KEY, base_url=URL)
DB_NAME              = "preprocessed_db"
COLLECTION_NAME      = "docs"
EMBEDDING_MODEL      = "text-embedding-3-large"
KNOWLEDGE_BASE_PATH  = Path("week05/knowledge-base")
AVERAGE_CHUNK_SIZE   = 500
VECTOR_RETRIEVAL_K   = 15
KEYWORD_RETRIEVAL_K  = 10
ANSWER_CONTEXT_K     = 5
CHROMA               = PersistentClient(path=DB_NAME)
REBUILD_DATABASE     = False


class Result(BaseModel):
    page_content: str
    metadata: dict


class Chunk(BaseModel):
    """Class to perfectly represent a chunk"""
    model_config = ConfigDict(populate_by_name=True)

    headline: str = Field(description="A brief heading for this chunk, typically a few words, that is most likely to be surfaced in a query")
    summary: str = Field(description="A few sentences summarizing the content of this chunk to answer common questions")
    original_text: str = Field(
        validation_alias=AliasChoices("original_text", "text"),
        description="The original text of this chunk from the provided document, exactly as is, not changed in any way"
    )

    def as_result(self, document):
        metadata = {"source": document["source"], "type": document["type"]}
        return Result(page_content=self.headline + "\n\n" + self.summary + "\n\n" + self.original_text,metadata=metadata)


class Chunks(BaseModel):
    chunks: list[Chunk]


def find_documents_with_keyword(
    keyword: str,
    limit: int = KEYWORD_RETRIEVAL_K,
) -> list[Result]:
    """
    Find chunks containing an exact keyword or phrase.

    Matching is case-insensitive.
    """
    collection = CHROMA.get_collection(COLLECTION_NAME)

    data = collection.get(
        include=["documents", "metadatas"]
    )

    keyword_lower = keyword.strip().lower()

    matches = []

    for document, metadata in zip(
        data["documents"],
        data["metadatas"],
    ):
        if keyword_lower in document.lower():
            matches.append(
                Result(
                    page_content=document,
                    metadata=metadata,
                )
            )

    return matches[:limit]


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_documents_with_keyword",
            "description": (
                "Search the knowledge base for chunks containing an exact "
                "keyword or named entity. Use this for names, locations, "
                "universities, awards, products, dates, acronyms, and other "
                "specific terms."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": (
                            "One distinctive keyword or short exact phrase "
                            "to search for, such as Manchester, IIOTY, "
                            "Jessica Liu, or Claimllm."
                        ),
                    }
                },
                "required": ["keyword"],
                "additionalProperties": False,
            },
        },
    }
]


def choose_retrieval_tool(question: str, history=None):
    history = history or []

    messages = [
        {
            "role": "system",
            "content": """
You retrieve information from the Insurellm knowledge base.

Use find_documents_with_keyword when the question contains a distinctive
name, organisation, university, location, award, product, acronym, date,
or exact phrase.

Call the tool with the smallest distinctive keyword likely to appear
verbatim in the source.

For semantic or conceptual questions that do not contain a useful exact
term, do not call the keyword tool.
""",
        },
        *history,
        {
            "role": "user",
            "content": question,
        },
    ]

    return completion(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        api_base=URL,
        temperature=0,
    )


def execute_tool_call(tool_call) -> list[Result]:
    function_name = tool_call.function.name

    if function_name != "find_documents_with_keyword":
        print(f"Unknown tool requested: {function_name}")
        return []

    try:
        arguments = json.loads(
            tool_call.function.arguments
        )
    except json.JSONDecodeError as exc:
        print(f"Invalid tool argument: {exc}")
        return []

    keyword = arguments.get("keyword", "").strip()

    if not keyword:
        print("Keyword tool called without keyword")
        return []

    return find_documents_with_keyword(
        keyword=keyword,
        limit=KEYWORD_RETRIEVAL_K
    )


def extract_json(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    start = min((i for i in (text.find("{"), text.find("[")) if i != -1), default=-1)
    if start == -1:
        raise ValueError(f"No JSON found in: {text[:200]}")
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(text[start:])   # ignores trailing junk
    return obj


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
You should divide up the document as you see fit, being sure that the entire document is returned in the chunks - don't leave anything out.
This document should probably be split into {how_many} chunks, but you can have more or less as appropriate.
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


def parse_chunks(data) -> Chunks:
    if isinstance(data, str):
        data = data.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(data)
    while isinstance(data, dict) and isinstance(data.get("chunks"), str):
        data = json.loads(data["chunks"])
    if isinstance(data, list):          # bare array, which is what you got
        data = {"chunks": data}
    return Chunks.model_validate(data)


def normalize(s: str) -> str:
    return " ".join(s.split())


def check_verbatim(chunks, document) -> int:
    source = normalize(document["text"])
    bad = 0
    for c in chunks:
        if normalize(c.original_text) not in source:
            print(f"⚠ not verbatim: {c.headline}")
            bad += 1
    return bad


def process_document(document):
    messages = make_messages(document)
    response = completion(
        model=MODEL,
        messages=messages,
        api_base=URL,
        response_format=Chunks,
    )
    reply = response.choices[0].message.content
    reply_clean = extract_json(reply)
    doc_as_chunks = parse_chunks(reply_clean).chunks
    # check_verbatim(doc_as_chunks, document)

    return [chunk.as_result(document) for chunk in doc_as_chunks]


def create_chunks(documents):
    """Create chunks"""
    chunks = []
    for doc in tqdm(documents):
        chunks.extend(process_document(doc))
    return chunks


def create_embeddings(chunks):
    if COLLECTION_NAME in [c.name for c in CHROMA.list_collections()]:
        CHROMA.delete_collection(COLLECTION_NAME)

    texts = [chunk.page_content for chunk in chunks]
    emb = OPENAI.embeddings.create(model=EMBEDDING_MODEL, input=texts).data
    vectors = [e.embedding for e in emb]

    collection = CHROMA.get_or_create_collection(COLLECTION_NAME)

    ids = [str(i) for i in range(len(chunks))]
    metas = [chunk.metadata for chunk in chunks]

    collection.add(ids=ids, embeddings=vectors, documents=texts, metadatas=metas)
    print(f"Vectorstore created with {collection.count()} documents")


class RankOrder(BaseModel):
    order: list[int] = Field(
        description="The order of relevance of chunks, from most relevant to least relevant, by chunk id number"
    )


def rerank(question, chunks):
    system_prompt = """
You are a document re-ranker.
You are provided with a question and a list of relevant chunks of text from a query of a knowledge base.
The chunks are provided in the order they were retrieved; this should be approximately ordered by relevance, but you may be able to improve on that.
You must rank order the provided chunks by relevance to the question, with the most relevant chunk first.
Reply only with the list of ranked chunk ids, nothing else. Include all the chunk ids you are provided with, reranked.
"""
    user_prompt = f"The user has asked the following question:\n\n{question}\n\nOrder all the chunks of text by relevance to the question, from most relevant to least relevant. Include all the chunk ids you are provided with, reranked.\n\n"
    user_prompt += "Here are the chunks:\n\n"
    for index, chunk in enumerate(chunks):
        user_prompt += f"# CHUNK ID: {index + 1}:\n\n{chunk.page_content}\n\n"
    user_prompt += "Reply only with the list of ranked chunk ids, nothing else."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = completion(
        model=MODEL,
        messages=messages,
        api_base=URL,
        response_format=RankOrder
    )
    reply = response.choices[0].message.content
    # print(f"Received reply (rerank): {reply}")
    order = RankOrder.model_validate_json(reply).order
    print(order)
    return [chunks[i - 1] for i in order]


def fetch_context_unranked(
    question: str,
    retrieval_k: int = VECTOR_RETRIEVAL_K) -> list[Result]:
    collection = CHROMA.get_collection(COLLECTION_NAME)
    collection_size = collection.count()

    if collection_size == 0:
        return []

    query_embedding = OPENAI.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[question],
    ).data[0].embedding

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(
            retrieval_k,
            collection_size,
        )
    )

    return [
        Result(
            page_content=document,
            metadata=metadata,
        )
        for document, metadata in zip(
            results["documents"][0],
            results["metadatas"][0],
        )
    ]


def fetch_context(question):
    chunks = fetch_context_unranked(question)
    return rerank(question, chunks)


SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant representing the company Insurellm.
You are chatting with a user about Insurellm.
Your answer will be evaluated for accuracy, relevance and completeness, so make sure it only answers the question and fully answers it.
If you don't know the answer, say so.
For context, here are specific extracts from the Knowledge Base that might be directly relevant to the user's question:
{context}

With this context, please answer the user's question. Be accurate, relevant and complete.
"""


def make_rag_messages(question, history, chunks):
    context = "\n\n".join(f"Extract from {chunk.metadata['source']}:\n{chunk.page_content}" for chunk in chunks)
    system_prompt = SYSTEM_PROMPT.format(context=context)
    return [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": question}]


def rewrite_query(
        question: str,
        history: list[dict] | None = None):
    history = history or []
    """Rewrite the user's question to be a more specific question that is more likely to surface relevant content in the Knowledge Base."""
    message = f"""
You are in a conversation with a user, answering questions about the company Insurellm.
You are about to look up information in a Knowledge Base to answer the user's question.

This is the history of your conversation so far with the user:
{history}

And this is the user's current question:
{question}

Respond only with a single, refined question that you will use to search the Knowledge Base.
It should be a VERY short specific question most likely to surface content. Focus on the question details.
Don't mention the company name unless it's a general question about the company.
IMPORTANT: Respond ONLY with the knowledgebase query, nothing else.
"""
    response = completion(
        model=MODEL,
        messages=[{"role": "system", "content": message}],
        api_base=URL
    )
    rewritten = response.choices[0].message.content.strip()
    rewritten = rewritten.strip('"').strip("'")
    return rewritten


def merge_chunks(*chunk_lists: list[Result]) -> list[Result]:
    """Combine the chunks from tool calling and vector embeddings and dedup"""
    merged = {}

    for chunk_list in chunk_lists:
        for chunk in chunk_list:
            key = (
                chunk.metadata.get("source"),
                chunk.page_content
            )
            merged[key] = chunk

    return list(merged.values())


def retrieve_with_tools(
    question: str,
    history: list[dict] | None = None) -> list[Result]:
    history = history or []

    response = choose_retrieval_tool(question, history)
    assistant_message = response.choices[0].message
    tool_calls = assistant_message.tool_calls or []

    retrieved = []

    for tool_call in tool_calls:
        retrieved.extend(
            execute_tool_call(tool_call)
        )

    return merge_chunks(retrieved)


def answer_question(
    question: str,
    history: list[dict] | None = None) -> tuple[str, list[Result]]:
    """
    Answer a question using hybrid keyword and vector retrieval.
    """
    history = history or []

    # Ask the model whether an exact keyword search is useful.
    keyword_chunks = retrieve_with_tools(
        question=question,
        history=history,
    )

    # Rewrite once for semantic retrieval.
    rewritten_query = rewrite_query(
        question,
        history,
    )

    vector_chunks = fetch_context_unranked(
        rewritten_query,
        retrieval_k=VECTOR_RETRIEVAL_K,
    )

    # Merge and remove duplicate chunks.
    combined_chunks = merge_chunks(
        keyword_chunks,
        vector_chunks,
    )

    # Rerank all combined candidates.
    if combined_chunks:
        reranked_chunks = rerank(
            question,
            combined_chunks,
        )
    else:
        reranked_chunks = []

    messages = make_rag_messages(
        question,
        history,
        reranked_chunks[:ANSWER_CONTEXT_K],
    )

    response = completion(
        model=MODEL,
        messages=messages,
        api_base=URL,
        temperature=0,
    )

    return (
        response.choices[0].message.content,
        reranked_chunks,
    )


if __name__ == "__main__":
    if REBUILD_DATABASE:
        print("Loading documents...")
        documents = fetch_documents()
        print(f"Total documents loaded: {len(documents)}")

        print("\nSample prompt:")
        print(make_prompt(documents[0]))
        # print(make_prompt(documents[1]))
        # print(make_prompt(documents[2]))

        print("\nSample message:")
        print(make_messages(documents[0]))

        print("\nChunk the entire set of documents")
        chunks = create_chunks(documents)

        print("\nCreating embeddings")
        create_embeddings(chunks)

    # print("\nTesting question:")
    # question = "Who went to Manchester University?"
    # print(question)
    # chunks = fetch_context_unranked(question)
    # # for chunk in chunks:
    # #     print(chunk.page_content[:20] + "...")
    # for index, c in enumerate(chunks):
    #     if "manchester" in c.page_content.lower():
    #         print(index)

    # print("\nReranking chunks:")
    # reranked = rerank(question, chunks)
    # for index, c in enumerate(reranked):
    #     if "manchester" in c.page_content.lower():
    #         print(index)

    # print(reranked[0].page_content)

    # q1 = "Who won the IIOTY award?"
    # print(f"\nQuestion: {q1}")
    # print(answer_question(q1, [])[0])

    q2 = "Who went to Manchester University?"
    print(f"\nQuestion: {q2}")
    print(answer_question(q2, [])[0])
