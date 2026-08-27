from pathlib import Path
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from langchain_core.documents import Document

from dotenv import load_dotenv

load_dotenv(override = True)

CHAT_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-large"
DB_NAME = "vector_db"
embeddings = OpenAIEmbeddings(model = EMBEDDING_MODEL)
RETRIEVAL_K = 5

System_prompt = """
You are a knowledgeable, friendly assistant representing the company Insurellm.
You are chatting with a user about Insurellm.
If relevant, use the given context to answer any question.
If you don't know the answer, say so, dont hallucinate and try to give answer
Context:
{context}
"""

vectorstore = Chroma(persist_directory = DB_NAME, embedding_function = embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K})
llm = ChatOpenAI(temperature = 0, model_name = CHAT_MODEL)

def fetch_context(question: str) -> list[Document]:
    """
    Retrieve relevant context documents for a question.
    """
    return retriever.invoke(question)

def combined_question(question: str, history: list[dict] = []) -> str:
    """
    Combine all the user's messages into a single string.
    """
    if not history:
        return question
    recent = history[-4:]  # last 2 turns
    history_text = "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in recent)
    prompt = (
        f"Given the conversation below, rewrite the follow-up question as a fully "
        f"self-contained question. Only include context from the history if it is "
        f"directly needed to understand the question. If the question is unrelated "
        f"to the history, return it unchanged.\n\n"
        f"History:\n{history_text}\n\n"
        f"Follow-up question: {question}\n\n"
        f"Standalone question:"
    )

    return llm.invoke(prompt).content

def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Document]]:
    """
    Answer the given question with RAG; return the answer and the context documents.
    """
    combined = combined_question(question, history)
    docs = fetch_context(combined)
    context = "\n\n".join(doc.page_content for doc in docs)
    system_prompt = System_prompt.format(context=context)
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(history))
    messages.append(HumanMessage(content=question))
    response = llm.invoke(messages)
    return response.content, docs