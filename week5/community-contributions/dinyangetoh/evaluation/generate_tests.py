import json
import random
from openai import OpenAI

from evaluation.test import TestQuestion

GENERATE_PROMPT = """You are creating evaluation examples for a RAG system over an institution/school website.

Given this chunk of text from the knowledge base, produce exactly one test example:
1. question: A short factual question that this chunk can answer (as a visitor would ask).
2. keywords: 3-6 exact phrases or numbers that should appear in retrieved context when answering (list of strings).
3. reference_answer: A concise answer drawn from the chunk (2-4 sentences).
4. category: One of: fees, admissions, general, programs, contact, or similar.

Chunk:
---
{chunk_text}
---

Reply with valid JSON only: {{"question": "...", "keywords": ["...", ...], "reference_answer": "...", "category": "..."}}"""


def generate_tests_from_vectorstore(
    vectorstore,
    client: OpenAI,
    model: str,
    max_tests: int = 10,
    seed: int | None = None,
) -> list[TestQuestion]:
    result = vectorstore._collection.get(include=["documents"])
    documents = result.get("documents") or []
    if not documents:
        return []

    indices = list(range(len(documents)))
    if seed is not None:
        rng = random.Random(seed)
        rng.shuffle(indices)
    else:
        random.shuffle(indices)
    indices = indices[:max_tests]

    tests: list[TestQuestion] = []
    for i in indices:
        chunk_text = (documents[i] or "")[:8000]
        if not chunk_text.strip():
            continue
        prompt = GENERATE_PROMPT.format(chunk_text=chunk_text)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        try:
            t = TestQuestion(
                question=str(data.get("question", "")).strip(),
                keywords=[str(x) for x in data.get("keywords", [])],
                reference_answer=str(data.get("reference_answer", "")).strip(),
                category=str(data.get("category", "general")).strip() or "general",
            )
            if t.question:
                tests.append(t)
        except Exception:
            continue
    return tests
