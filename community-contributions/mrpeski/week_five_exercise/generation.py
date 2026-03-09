from pathlib import Path
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv(override=True)

MODEL      = "gpt-4.1-nano"
DB_NAME    = str(Path(__file__).parent / "db" / "vector_db")
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
RETRIEVAL_K = 10

SYSTEM_PROMPT = """
You are a technical assistant helping a React freelancer answer questions
about their clients' pinned package versions and tech stacks.
You have access to a registry of clients, each with their exact package
versions, slugs, and architectural notes.
Use the given context to answer questions precisely. When referencing versions,
always be exact. If a client is not in the context, say so.
Context:
{context}
"""


def _ensure_vectorstore() -> Chroma:
    """
    Return the vectorstore, running ingestion first if the DB doesn't exist yet.
    """
    if not Path(DB_NAME).exists():
        print("Vector DB not found — running ingestion...")
        from db.ingest import fetch_documents, create_chunks, create_embeddings
        documents = fetch_documents()
        chunks    = create_chunks(documents)
        create_embeddings(chunks)
        print("Ingestion complete")

    return Chroma(persist_directory=DB_NAME, embedding_function=embeddings)


vectorstore = _ensure_vectorstore()
retriever   = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K})
llm         = ChatOpenAI(temperature=0, model_name=MODEL)


def fetch_context(question: str) -> list[Document]:
    """
    Retrieve relevant context documents for a question.
    """
    return retriever.invoke(question)


def combined_question(question: str, history: list[dict] = []) -> str:
    """
    Combine all the user's messages into a single string.
    """
    prior = "\n".join(m["content"] for m in history if m["role"] == "user")
    return (prior + "\n" + question).strip()


def answer_question(
    question: str, history: list[dict] = []
) -> tuple[str, list[Document]]:
    """
    Answer the given question with RAG; return the answer and the context documents.
    """
    combined = combined_question(question, history)
    docs     = fetch_context(combined)
    context  = "\n\n".join(doc.page_content for doc in docs)

    system_prompt = SYSTEM_PROMPT.format(context=context)
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(history))
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)
    return response.content, docs