"""Answer generation: reranking, context assembly, and final LLM response."""
from config import (
    ANSWER_CONTEXT_K,
    MODEL,
    URL,
    VECTOR_RETRIEVAL_K
)
from litellm import completion
from retrieval import (
    retrieve_with_tools,
    rewrite_query,
    fetch_context_unranked,
    merge_chunks,
    rerank,
)


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
    """Build the full message list for the answer-generation LLM call.

    Assembles the system prompt with context extracts, appends conversation
    history, and adds the user's question.
    """
    context = "\n\n".join(
        f"Extract from {chunk.metadata['source']}:\n{chunk.page_content}"
        for chunk in chunks
    )
    system_prompt = SYSTEM_PROMPT.format(context=context)
    return [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": question}]


def answer_question(
    question: str,
    history: list[dict] | None = None,
) -> tuple[str, list]:
    """Answer a question using hybrid keyword and vector retrieval.

    Pipeline:
      1. Tool-based keyword retrieval (LLM decides if keyword search is useful)
      2. Query rewriting for semantic retrieval
      3. Vector similarity search
      4. Merge and deduplicate results
      5. Rerank all candidates by relevance
      6. Generate final answer with top-K reranked chunks

    Returns a tuple of (answer_text, reranked_chunks).
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
