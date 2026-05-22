import os
import json
import numpy as np

from dotenv import load_dotenv
from langchain_core.documents import Document
from openai import OpenAI
from supabase import create_client
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings


load_dotenv()
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_INSURLLM_RAG_URL")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI()
MODEL="text-embedding-3-large"

def embed(text):
    return openai_client.embeddings.create(
        input=text, model=MODEL, dimensions=1536
    ).data[0].embedding

# --- 1. INGEST: accepts LangChain Document objects ---

def ingest(documents: list[Document]):
    rows = [
        {
            "content": doc.page_content,
            "embedding": embed(doc.page_content),
            "source": doc.metadata.get("source"),
            "metadata": doc.metadata          # stores full metadata as JSONB
        }
        for doc in documents
    ]
    supabase.table("documents").insert(rows).execute()

# --- 2. RETRIEVE: returns Document objects so shape is consistent throughout ---

def retrieve(query: str, match_count: int = 5, filter: dict = {}) -> list[Document]:
    result = supabase.rpc("match_documents", {
        "query_embedding": embed(query),
        "match_count": match_count,
        "filter": filter
    }).execute()

    return [
        Document(
            page_content=r["content"],
            metadata=(r.get("metadata") or {}) | {"similarity": r["similarity"]}
        )
        for r in result.data
    ]

# --- 3. GENERATE ---

def rag(query: str, filter: dict = {}) -> str:
    docs = retrieve(query, filter=filter)
    context = "\n\n".join(
        f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )

    response = openai_client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Answer using only the provided context. "
                    "If the answer isn't in the context, say you don't know."
                )
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}"
            }
        ]
    )
    return response.choices[0].message.content


# --- 1. Fetch vectors from Supabase ---

def fetch_vectors() -> tuple[list[str], list[str], np.ndarray]:
    result = supabase.table("documents") \
        .select("content, source, embedding, metadata") \
        .execute()

    contents = [r["content"][:60] + "..." for r in result.data]
    sources  = [(r.get("metadata") or {}).get("doc_type", "unknown") for r in result.data]
    
    # Parse string embeddings to float arrays
    vectors = np.array([
        json.loads(r["embedding"]) if isinstance(r["embedding"], str) else r["embedding"]
        for r in result.data
    ], dtype=np.float32)

    return contents, sources, vectors


# --- Return the vectorstore object that can be used by the retriever

def get_vectorstore():
    embeddings = OpenAIEmbeddings(model=MODEL)

    vectorstore = SupabaseVectorStore(
        client=supabase,
        embedding=embeddings,
        table_name="documents",
        query_name="match_documents"
    )

    return vectorstore