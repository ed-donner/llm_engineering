import os
from pathlib import Path
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from litellm import completion
from dotenv import load_dotenv

load_dotenv(override=True)

ANSWER_MODEL = "openrouter/openai/gpt-4o-mini"
UTILITY_MODEL = "openrouter/openai/gpt-4o-mini"
DB_NAME = str(Path(__file__).parent.parent / "vector_db")

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    encode_kwargs={"normalize_embeddings": True},
)
RETRIEVAL_K = 15

SYSTEM_PROMPT = """You are a knowledgeable, friendly assistant representing Insurellm, an Insurance Tech company.
You answer questions about Insurellm using ONLY the provided context.

CRITICAL INSTRUCTIONS:
- Include ALL relevant facts, names, numbers, dates, and details from the context
- Be thorough and complete — do not omit any relevant information from the context
- Answer ONLY what is asked — do not add information beyond what's relevant to the question
- If the context doesn't contain the answer, say you don't know
- Use specific details from the context rather than general statements

Context:
{context}"""


vectorstore = Chroma(persist_directory=DB_NAME, embedding_function=embeddings)
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": RETRIEVAL_K, "fetch_k": 40},
)


def rewrite_query(question: str) -> str:
    """Rewrite the question for better vector similarity search."""
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "Rewrite the user's question into a short, specific search query "
                    "optimized for vector similarity search against a company knowledge base. "
                    "Focus on key entities, names, and facts. Output ONLY the rewritten query."
                ),
            },
            {"role": "user", "content": question},
        ]
        response = completion(model=UTILITY_MODEL, messages=messages)
        rewritten = response.choices[0].message.content.strip()
        return rewritten if rewritten else question
    except Exception:
        return question


def fetch_context(question: str) -> list[Document]:
    """Retrieve relevant context with query rewriting."""
    rewritten = rewrite_query(question)
    return retriever.invoke(rewritten)


def combined_question(question: str, history: list[dict] = []) -> str:
    prior = "\n".join(m["content"] for m in history if m["role"] == "user")
    return prior + "\n" + question if prior else question


def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Document]]:
    """Answer the given question with RAG."""
    combined = combined_question(question, history)
    docs = fetch_context(combined)
    context = "\n\n".join(
        f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )
    system_prompt = SYSTEM_PROMPT.format(context=context)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})

    response = completion(model=ANSWER_MODEL, messages=messages)
    return response.choices[0].message.content, docs
