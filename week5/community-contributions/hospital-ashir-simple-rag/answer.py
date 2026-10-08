"""
RAG answering layer for the Hospital-Ashir knowledge base.

Loads the Chroma vector store produced by `ingest.py` and answers questions
about Ashir General Hospital, its doctors, patients, and disease programs.
"""

from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from langchain_core.documents import Document


load_dotenv(override=True)

MODEL = "gpt-4.1-nano"
EMBEDDING_MODEL = "text-embedding-3-large"

BASE_DIR = Path(__file__).parent
DB_NAME = str(BASE_DIR / "vector_db")

RETRIEVAL_K = 14

SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant for Ashir General Hospital.
You help staff and authorized users answer questions about:
  - the hospital itself (departments, facilities, services),
  - its doctors (specialties, credentials, availability),
  - its patients (case files, care plans, medications),
  - and the diseases and conditions the hospital treats.

Use ONLY the given context to answer. Quote specific doctors, patient IDs,
departments, or conditions when they appear in the context. If the answer is
not in the context, say you don't have that information.

Remind users that all patient data is confidential — summarize rather than
expose personal details unless the question clearly requires them.

Context:
{context}
"""

vectorstore = Chroma(
    persist_directory=DB_NAME,
    embedding_function=OpenAIEmbeddings(model=EMBEDDING_MODEL),
)
retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K})
llm = ChatOpenAI(temperature=0, model_name=MODEL)


def fetch_context(question: str) -> list[Document]:
    """Retrieve relevant context documents for a question."""
    return retriever.invoke(question)


def combined_question(question: str, history: list[dict] = []) -> str:
    """Combine all of the user's prior messages with the new question."""
    prior = "\n".join(m["content"] for m in history if m["role"] == "user")
    return (prior + "\n" + question).strip()


def answer_question(
    question: str, history: list[dict] = []
) -> tuple[str, list[Document]]:
    """
    Answer a question using RAG over the Hospital-Ashir knowledge base.
    Returns the generated answer and the retrieved context documents.
    """
    combined = combined_question(question, history)
    docs = fetch_context(combined)
    context = "\n\n".join(doc.page_content for doc in docs)

    system_prompt = SYSTEM_PROMPT.format(context=context)
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(history))
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)
    return response.content, docs


if __name__ == "__main__":
    sample_questions = [
        "Who is the chair of Cardiology and what are their credentials?",
        "What services does Ashir offer for Type 2 Diabetes patients?",
        "Tell me about patient ASH-10456's treatment plan.",
        "How many beds does the hospital have and across which units?",
    ]

    for q in sample_questions:
        print("\n" + "=" * 80)
        print(f"Q: {q}")
        answer, sources = answer_question(q)
        print(f"\nA: {answer}")
        unique_sources = sorted(
            {Path(d.metadata.get("source", "")).name for d in sources}
        )
        print(f"\nSources ({len(unique_sources)}):")
        for s in unique_sources:
            print(f"  - {s}")
