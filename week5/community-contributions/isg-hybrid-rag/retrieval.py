"""Retrieval strategies: vector search, keyword search, query rewriting, and tool-based retrieval."""
import json

from litellm import completion
from config import (
    MODEL,
    URL,
    OPENAI,
    COLLECTION_NAME,
    CHROMA,
    EMBEDDING_MODEL,
    KEYWORD_RETRIEVAL_K,
    VECTOR_RETRIEVAL_K,
)
from models import Result, RankOrder


# --- Tool definitions for LLM-based retrieval ---
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


def find_documents_with_keyword(
    keyword: str,
    limit: int = KEYWORD_RETRIEVAL_K,
) -> list[Result]:
    """Find chunks containing an exact keyword or phrase.

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


def fetch_context_unranked(
    question: str,
    retrieval_k: int = VECTOR_RETRIEVAL_K,
) -> list[Result]:
    """Perform vector similarity search in ChromaDB and return unranked results."""
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
    """Fetch and rerank context using vector search + LLM reranking."""
    chunks = fetch_context_unranked(question)
    return rerank(question, chunks)


def rewrite_query(
    question: str,
    history: list[dict] | None = None,
):
    """Rewrite the user's question to be more specific for better retrieval.

    Uses the LLM to generate a refined query that is more likely to surface
    relevant content in the Knowledge Base.
    """
    history = history or []
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
        api_base=URL,
    )
    rewritten = response.choices[0].message.content.strip()
    rewritten = rewritten.strip('"').strip("'")
    return rewritten


def choose_retrieval_tool(question: str, history=None):
    """Ask the LLM whether a keyword search is useful for the given question.

    Returns the LLM's tool call response (or None if no tool should be called).
    """
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
    """Execute a single LLM tool call and return the results."""
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
        limit=KEYWORD_RETRIEVAL_K,
    )


def retrieve_with_tools(
    question: str,
    history: list[dict] | None = None,
) -> list[Result]:
    """Use LLM tool-calling to decide when and how to do keyword retrieval.

    The LLM decides whether a keyword search is useful and which keyword to use.
    Returns the merged results from any tool calls made.
    """
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


# --- Reranking ---
RERANK_SYSTEM_PROMPT = """
You are a document re-ranker.
You are provided with a question and a list of relevant chunks of text from a query of a knowledge base.
The chunks are provided in the order they were retrieved; this should be approximately ordered by relevance, but you may be able to improve on that.
You must rank order the provided chunks by relevance to the question, with the most relevant chunk first.
Reply only with the list of ranked chunk ids, nothing else. Include all the chunk ids you are provided with, reranked.
"""


def rerank(question, chunks):
    """Rerank a list of chunks by relevance to the question using an LLM."""
    user_prompt = f"The user has asked the following question:\n\n{question}\n\nOrder all the chunks of text by relevance to the question, from most relevant to least relevant. Include all the chunk ids you are provided with, reranked.\n\n"
    user_prompt += "Here are the chunks:\n\n"
    for index, chunk in enumerate(chunks):
        user_prompt += f"# CHUNK ID: {index + 1}:\n\n{chunk.page_content}\n\n"
    user_prompt += "Reply only with the list of ranked chunk ids, nothing else."
    messages = [
        {"role": "system", "content": RERANK_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    response = completion(
        model=MODEL,
        messages=messages,
        api_base=URL,
        response_format=RankOrder,
    )
    reply = response.choices[0].message.content
    # print(f"Received reply (rerank): {reply}")
    order = RankOrder.model_validate_json(reply).order
    print(order)

    # The model can hallucinate ids: drop out-of-range ones and append any
    # chunk it forgot, so we never crash and never silently lose a chunk.
    seen = set()
    ranked = []
    for i in order:
        if 1 <= i <= len(chunks) and i not in seen:
            seen.add(i)
            ranked.append(chunks[i - 1])
    ranked.extend(chunk for index, chunk in enumerate(chunks, start=1) if index not in seen)
    return ranked


def merge_chunks(*chunk_lists: list[Result]) -> list[Result]:
    """Combine chunks from multiple retrieval strategies and deduplicate.

    Deduplication is based on (source, page_content) pairs.
    """
    merged = {}

    for chunk_list in chunk_lists:
        for chunk in chunk_list:
            key = (
                chunk.metadata.get("source"),
                chunk.page_content
            )
            merged[key] = chunk

    return list(merged.values())
