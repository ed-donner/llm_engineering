"""Enhanced RAG answer pipeline with hybrid retrieval.

Dual vector search + LLM reranking + keyword search supplement.
Uses enhanced_db (pre-computed summaries) for better coverage.
"""

import re
from openai import OpenAI
from dotenv import load_dotenv
from chromadb import PersistentClient
from litellm import completion
from pydantic import BaseModel, Field
from pathlib import Path
from tenacity import retry, wait_exponential


load_dotenv(override=True)

UTILITY_MODEL = "groq/openai/gpt-oss-120b"
ANSWER_MODEL = "groq/openai/gpt-oss-120b"

# Paths relative to week5/ directory (where this is typically run from)
WEEK5_DIR = Path(__file__).parent.parent.parent.parent / "week5"
DB_NAME = str(WEEK5_DIR / "enhanced_db")
KNOWLEDGE_BASE_PATH = WEEK5_DIR / "knowledge-base"

collection_name = "docs"
embedding_model = "text-embedding-3-large"
wait = wait_exponential(multiplier=1, min=10, max=240)

RETRIEVAL_K = 20
FINAL_K = 12

openai = OpenAI()
chroma = PersistentClient(path=DB_NAME)
collection = chroma.get_or_create_collection(collection_name)

SYSTEM_PROMPT = """You are a knowledgeable, friendly assistant representing the company Insurellm.
You are chatting with a user about Insurellm.
Your answer will be evaluated for accuracy, completeness, and relevance.

RULES:
- Answer the question fully and directly using ONLY the context below.
- Include all relevant facts, figures, names, and dates from the context.
- Do not add information not found in the context.
- Do not include tangential details that don't directly answer the question.
- If the question asks for totals or aggregates, list each component with its value and compute the sum.
- If you don't know the answer from the context, say so clearly.

Context:
{context}
"""


class Result(BaseModel):
    page_content: str
    metadata: dict


class RankOrder(BaseModel):
    order: list[int] = Field(
        description="The order of relevance of chunks, from most relevant to least relevant, by chunk id number"
    )


_kb_documents = None


def _load_kb_documents():
    """Load and cache KB documents with paragraph splits for keyword search."""
    global _kb_documents
    if _kb_documents is not None:
        return _kb_documents

    _kb_documents = []
    for folder in KNOWLEDGE_BASE_PATH.iterdir():
        if not folder.is_dir():
            continue
        doc_type = folder.name
        for file in folder.rglob("*.md"):
            text = file.read_text(encoding="utf-8")
            paragraphs = []
            for para in re.split(r"\n\n+", text):
                para = para.strip()
                if len(para) >= 30:
                    paragraphs.append(para)
            _kb_documents.append({
                "full_text": text,
                "paragraphs": paragraphs,
                "source": file.as_posix(),
                "type": doc_type,
            })
    return _kb_documents


STOP_WORDS = {
    "what", "is", "the", "a", "an", "of", "in", "for", "to", "and", "or",
    "how", "many", "much", "does", "did", "do", "was", "were", "has", "have",
    "who", "when", "where", "which", "that", "this", "these", "those",
    "by", "at", "on", "with", "from", "per", "its", "all", "are", "it",
    "about", "their", "currently", "total", "across", "according", "can",
    "been", "had", "would", "could", "should", "will", "shall", "may",
    "not", "no", "yes", "if", "but", "so", "than", "then", "each",
    "any", "some", "other", "into", "over", "under", "between", "after",
    "before", "during", "since", "also", "more", "most", "such", "very",
    "just", "only", "own", "same", "both", "few", "new", "old", "long",
}


def extract_specific_terms(question):
    """Extract dollar amounts, percentages, product names, and proper nouns."""
    terms = []
    for match in re.finditer(r"\$[\d,.]+[MBK]?", question):
        terms.append(match.group(0))
    for match in re.finditer(r"\d+%", question):
        terms.append(match.group(0))
    for match in re.finditer(r"\b\w*llm\b", question, re.IGNORECASE):
        terms.append(match.group(0))
    for match in re.finditer(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", question):
        name = match.group(0)
        if name.lower() not in STOP_WORDS and len(name) > 2:
            terms.append(name)
    return list(dict.fromkeys(terms))


def keyword_search(question, max_results=8):
    """Find KB paragraphs matching specific terms from the question."""
    documents = _load_kb_documents()
    specific_terms = extract_specific_terms(question)

    if not specific_terms:
        return []

    doc_scores = [
        (sum(1 for t in specific_terms if t.lower() in doc["full_text"].lower()), doc)
        for doc in documents
        if any(t.lower() in doc["full_text"].lower() for t in specific_terms)
    ]
    doc_scores.sort(key=lambda x: -x[0])

    results = []
    seen = set()

    for hits, doc in doc_scores[:4]:
        if doc["type"] == "contracts":
            for para in doc["paragraphs"]:
                if "**Title**" in para and "Date" in para and "Insurellm" in para:
                    key = para[:120].lower()
                    if key not in seen:
                        seen.add(key)
                        results.append(Result(
                            page_content=para,
                            metadata={"source": doc["source"], "type": doc["type"]},
                        ))
                    break

        doc_results = []
        for para in doc["paragraphs"]:
            p_lower = para.lower()
            p_hits = sum(1 for t in specific_terms if t.lower() in p_lower)
            if p_hits > 0:
                key = para[:120].lower()
                if key not in seen:
                    doc_results.append((p_hits, para, key))

        doc_results.sort(key=lambda x: -x[0])
        for _, para, key in doc_results[:5]:
            seen.add(key)
            results.append(Result(
                page_content=para,
                metadata={"source": doc["source"], "type": doc["type"]},
            ))

        if len(results) >= max_results:
            break

    return results[:max_results]


@retry(wait=wait)
def rerank(question, chunks):
    """LLM-based reranking of retrieved chunks by relevance."""
    if len(chunks) <= 1:
        return chunks

    system_prompt = """You are a document re-ranker.
You are provided with a question and a list of relevant chunks of text from a query of a knowledge base.
The chunks are provided in the order they were retrieved; this should be approximately ordered by relevance, but you may be able to improve on that.
You must rank order the provided chunks by relevance to the question, with the most relevant chunk first.
Reply only with the list of ranked chunk ids, nothing else. Include all the chunk ids you are provided with, reranked."""

    user_prompt = f"The user has asked the following question:\n\n{question}\n\nOrder all the chunks of text by relevance to the question, from most relevant to least relevant. Include all the chunk ids you are provided with, reranked.\n\nHere are the chunks:\n\n"
    for index, chunk in enumerate(chunks):
        user_prompt += f"# CHUNK ID: {index + 1}:\n\n{chunk.page_content}\n\n"
    user_prompt += "Reply only with the list of ranked chunk ids, nothing else."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = completion(model=UTILITY_MODEL, messages=messages, response_format=RankOrder)
    reply = response.choices[0].message.content
    order = RankOrder.model_validate_json(reply).order

    reranked = [chunks[i - 1] for i in order if 1 <= i <= len(chunks)]
    reranked += [c for c in chunks if c not in reranked]
    return reranked


@retry(wait=wait)
def rewrite_query(question, history=[]):
    """Rewrite the user's question for better KB retrieval."""
    message = f"""You are in a conversation with a user, answering questions about the company Insurellm.
You are about to look up information in a Knowledge Base to answer the user's question.

This is the history of your conversation so far with the user:
{history}

And this is the user's current question:
{question}

Respond only with a short, refined question that you will use to search the Knowledge Base.
It should be a VERY short specific question most likely to surface content. Focus on the question details.
IMPORTANT: Respond ONLY with the precise knowledgebase query, nothing else."""

    response = completion(model=UTILITY_MODEL, messages=[{"role": "system", "content": message}])
    return response.choices[0].message.content


def vector_search(query, k=RETRIEVAL_K):
    """Embedding-based search against ChromaDB."""
    embedding = openai.embeddings.create(model=embedding_model, input=[query]).data[0].embedding
    results = collection.query(query_embeddings=[embedding], n_results=k)
    chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append(Result(page_content=doc, metadata=meta))
    return chunks


def merge_chunks(chunks1, chunks2):
    """Merge two chunk lists, deduplicating. First list has priority."""
    merged = chunks1[:]
    existing = {chunk.page_content[:150].lower().strip() for chunk in chunks1}
    for chunk in chunks2:
        key = chunk.page_content[:150].lower().strip()
        if key not in existing:
            existing.add(key)
            merged.append(chunk)
    return merged


def make_rag_messages(question, history, chunks):
    """Build the message list for the answer LLM."""
    context = "\n\n".join(
        f"Extract from {chunk.metadata['source']}:\n{chunk.page_content}" for chunk in chunks
    )
    system_prompt = SYSTEM_PROMPT.format(context=context)
    return (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": question}]
    )


def fetch_context(original_question):
    """Hybrid retrieval: dual vector search + reranking + keyword supplement."""
    rewritten = rewrite_query(original_question)
    v1 = vector_search(original_question, k=RETRIEVAL_K)
    v2 = vector_search(rewritten, k=RETRIEVAL_K)
    reranked = rerank(original_question, merge_chunks(v1, v2)[:25])
    return merge_chunks(reranked[:FINAL_K], keyword_search(original_question, max_results=8))


@retry(wait=wait)
def answer_question(question: str, history: list[dict] = []) -> tuple[str, list]:
    """Answer a question using hybrid RAG. Returns (answer, context_chunks)."""
    chunks = fetch_context(question)
    response = completion(model=ANSWER_MODEL, messages=make_rag_messages(question, history, chunks))
    return response.choices[0].message.content, chunks
