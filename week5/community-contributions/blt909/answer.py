from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from langchain_core.documents import Document

from dotenv import load_dotenv


load_dotenv(override=True)

MODEL = "gemini-3-flash-preview"
DB_NAME = str(Path(__file__).parent / "rst_doc_db")

embeddings = HuggingFaceEmbeddings(model="google/embeddinggemma-300M")
RETRIEVAL_K = 10

SYSTEM_PROMPT = """
You are a knowledgeable, precise and meticulous technical mentor specialized in {repo}.
You are chatting with a user about technical documentation.
Always use the given context to answer any question.
If the context is empty, ask if you can answer with your own knowledge.
If the context is not empty, you can enhance your answer with your own knowledge, but you need to specify that explicitly.

Context:
{context}
"""


llm = ChatGoogleGenerativeAI(temperature=1, model=MODEL)


def fetch_context(question: str, repo: str) -> list[Document]:
    """
    Retrieve relevant context documents for a question.
    """
    vectorstore = Chroma(persist_directory=DB_NAME, collection_name=repo, embedding_function=embeddings)
    retriever = vectorstore.as_retriever()

    return retriever.invoke(question, k=RETRIEVAL_K)


def combined_question(question: str, history: list[dict] = []) -> str:
    """
    Combine all the user's messages into a single string.
    """
    prior = "\n".join(m["content"] for m in history if m["role"] == "user")
    return prior + "\n" + question


def answer_question(question: str, repo: str, history: list[dict] = []) -> tuple[str, list[Document]]:
    """
    Answer the given question with RAG; return the answer and the context documents.
    """
    combined = combined_question(question, history)
    docs = fetch_context(combined, repo)
    context = "\n\n".join(doc.page_content for doc in docs)
    system_prompt = SYSTEM_PROMPT.format(context=context, repo=repo)    
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(history))
    messages.append(HumanMessage(content=question))
    response = llm.invoke(messages)
    return response.content[0]['text'], docs
