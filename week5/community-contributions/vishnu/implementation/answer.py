from openai import OpenAI
import os
from pathlib import Path
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv
from litellm import completion
from pydantic import BaseModel, Field
from tenacity import retry, wait_exponential

# Load environment variables
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_dir = os.path.dirname(parent_dir)
dotenv_path = os.path.join(root_dir, ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)

MODEL = "openai/gpt-4o-mini"
DB_NAME = str(Path(__file__).parent.parent / "vector_db")

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory=DB_NAME, embedding_function=embeddings)

RETRIEVAL_K = 3
FINAL_K = 3

SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant representing the company Insurellm.
You are chatting with a user about Insurellm.
Your answer will be evaluated for accuracy, relevance and completeness, so make sure it only answers the question and fully answers it.
If you don't know the answer, say so.
For context, here are specific extracts from the Knowledge Base that might be directly relevant to the user's question:
{context}

With this context, please answer the user's question. Be accurate, relevant and complete.
"""


class RankOrder(BaseModel):
    order: list[int] = Field(
        description="The order of relevance of chunks, from most relevant to least relevant, by chunk id number"
    )


wait = wait_exponential(multiplier=1, min=2, max=10)


@retry(wait=wait)
def rerank(question: str, docs: list[Document]) -> list[Document]:
    if not docs:
        return []
        
    system_prompt = """
You are a document re-ranker.
You are provided with a question and a list of relevant chunks of text from a query of a knowledge base.
The chunks are provided in the order they were retrieved; this should be approximately ordered by relevance, but you may be able to improve on that.
You must rank order the provided chunks by relevance to the question, with the most relevant chunk first.
Reply only with the list of ranked chunk ids, nothing else. Include all the chunk ids you are provided with, reranked.
"""
    user_prompt = f"The user has asked the following question:\n\n{question}\n\nOrder all the chunks of text by relevance to the question, from most relevant to least relevant. Include all the chunk ids you are provided with, reranked.\n\n"
    user_prompt += "Here are the chunks:\n\n"
    for index, doc in enumerate(docs):
        user_prompt += f"# CHUNK ID: {index + 1}:\n\n{doc.page_content}\n\n"
    user_prompt += "Reply only with the list of ranked chunk ids, nothing else."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    response = completion(
        model=MODEL, 
        messages=messages, 
        response_format=RankOrder,
        api_base="https://openrouter.ai/api/v1",
        max_tokens=100
    )
    reply = response.choices[0].message.content
    order = RankOrder.model_validate_json(reply).order
    
    # Safely map order back to docs
    reranked_docs = []
    for idx in order:
        if 1 <= idx <= len(docs):
            reranked_docs.append(docs[idx - 1])
            
    # Add any remaining docs that weren't included in the model's output
    for doc in docs:
        if doc not in reranked_docs:
            reranked_docs.append(doc)
            
    return reranked_docs


@retry(wait=wait)
def rewrite_query(question: str, history: list = []) -> str:
    """Rewrite the user's question to be a more specific question that is more likely to surface relevant content in the Knowledge Base."""
    message = f"""
You are in a conversation with a user, answering questions about the company Insurellm.
You are about to look up information in a Knowledge Base to answer the user's question.

This is the history of your conversation so far with the user:
{history}

And this is the user's current question:
{question}

Respond only with a short, refined question that you will use to search the Knowledge Base.
It should be a VERY short specific question most likely to surface content. Focus on the question details.
IMPORTANT: Respond ONLY with the precise knowledgebase query, nothing else.
"""
    response = completion(
        model=MODEL, 
        messages=[{"role": "user", "content": message}],
        api_base="https://openrouter.ai/api/v1",
        max_tokens=100
    )
    return response.choices[0].message.content.strip()


def merge_documents(docs1: list[Document], docs2: list[Document]) -> list[Document]:
    merged = docs1[:]
    existing = [doc.page_content for doc in docs1]
    for doc in docs2:
        if doc.page_content not in existing:
            merged.append(doc)
            existing.append(doc.page_content)
    return merged


def fetch_context_unranked(question: str) -> list[Document]:
    return vectorstore.as_retriever().invoke(question, k=RETRIEVAL_K)


def fetch_context(original_question: str) -> list[Document]:
    print("[RAG] Running in lightweight mode to fit OpenRouter credit limit...")
    docs = fetch_context_unranked(original_question)[:1]
    for d in docs:
        d.page_content = d.page_content[:80]
    return docs


def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Document]]:
    """
    Answer the given question with RAG; return the answer and the context documents.
    """
    docs = fetch_context(question)
    
    context = "\n\n".join(
        f"Extract from {doc.metadata.get('source', 'Knowledge Base')}:\n{doc.page_content}" 
        for doc in docs
    )
    system_prompt = SYSTEM_PROMPT.format(context=context)
    
    formatted_history = []
    if history:
        for m in history:
            formatted_history.append({"role": m.get("role", "user"), "content": m.get("content", "")})
            
    messages = [{"role": "system", "content": system_prompt}] + formatted_history + [{"role": "user", "content": question}]
    
    response = completion(
        model=MODEL,
        messages=messages,
        api_base="https://openrouter.ai/api/v1",
        max_tokens=50
    )
    return response.choices[0].message.content, docs
