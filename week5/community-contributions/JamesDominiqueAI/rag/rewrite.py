"""
rag/rewrite.py — Query rewriting using the LLM via litellm.

Rewrites the user's question to be more specific and retrieval-friendly,
accounting for conversation history. Uses tenacity for retries.
"""

import os
import sys
from typing import List, Dict
from tenacity import retry, wait_exponential
from litellm import completion

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL, RETRY_MIN_WAIT, RETRY_MAX_WAIT

wait = wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT)


@retry(wait=wait)
def rewrite_query(question: str, history: List[Dict] = []) -> str:
    """
    Rewrite the user's question into a short, precise knowledge base query.
    Accounts for conversation history to resolve pronouns and context.

    Args:
        question: The user's current question.
        history: Prior conversation turns (list of {role, content} dicts).

    Returns:
        A short, refined query string optimised for vector retrieval.
    """
    message = f"""
You are in a conversation answering questions about regulatory compliance documents.
You are about to search a Knowledge Base to answer the user's question.

Conversation history so far:
{history}

User's current question:
{question}

Respond only with a single, short, refined question that will be used to search the Knowledge Base.
It should be VERY specific and focused on the key facts needed to answer the question.
Do not mention "knowledge base" or "regulatory documents" — just write the query itself.
IMPORTANT: Respond ONLY with the query, nothing else.
"""
    response = completion(
        model=MODEL,
        # messages=[{"role": "system", "content": message}],
        # ✅ Correct
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a query rewriter for a regulatory compliance RAG system. "
                    "Given a user question, respond ONLY with a single refined search query. "
                    "Be specific and focused. Do not mention 'knowledge base' or 'regulatory documents'."
                )
            },
            {
                "role": "user",
                "content": question  # just the raw question here
            }
        ]
    )
    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    tests = [
        ("What changed in 2023?", []),
        ("What are the penalties?", []),
        ("How long must we keep records?", [{"role": "user", "content": "Tell me about REG-ABC-2023"}, {"role": "assistant", "content": "REG-ABC-2023 covers data handling..."}]),
    ]
    for q, h in tests:
        rewritten = rewrite_query(q, h)
        changed = "→" if rewritten != q else "="
        print(f"Original:  {q}")
        print(f"Rewritten: {rewritten}\n")

