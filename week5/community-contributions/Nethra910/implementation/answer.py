import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from langchain_core.documents import Document



load_dotenv(override=True)
groq_api_key = os.getenv("GROQ_API_KEY")
MODEL = "openai/gpt-oss-120b"

DB_NAME = str(Path(__file__).parent.parent / "vector_db")
# print(DB_NAME)
embeddings = HuggingFaceEmbeddings(model_name = "all-MiniLM-L6-v2")
RETRIEVAL_K = 10

SYSTEM_PROMPT = """

You are a knowledgeable and friendly assistant for CloudWay.
You are chatting with a user about CloudWay.
Use the provided context to answer the user's questions accurately.
If the answer can be found in the context, use that information.
If the answer is not available in the context, clearly say that you don't know the answer.
Do not make up or assume information.

Context:
{context}

"""

vectorstore = Chroma(
    embedding_function = embeddings, 
    persist_directory = DB_NAME
)
retriever = vectorstore.as_retriever(
    search_kwargs={"k": RETRIEVAL_K}
)
print("GROQ Key Exists: ",groq_api_key[0:4] + "..." + groq_api_key[-2:])
print("MODEL : ",MODEL)

llm = ChatGroq(
    temperature=0,
    api_key = groq_api_key,
    model = MODEL
)

def fetch_context(question: str) -> list[Document]:
    """
    Retrieve relevant context documents for a question.
    """
    return retriever.invoke(question)


def combined_question(question: str, history: list[dict] | None = None) -> str:
    if history is None:
        history = []

    prior_messages = []

    for message in history:
        if message["role"] == "user":
            content = message["content"]

            if isinstance(content, str):
                prior_messages.append(content)

            elif isinstance(content, list):
                text = ""

                for item in content:
                    if isinstance(item, str):
                        text += item
                    elif isinstance(item, dict):
                        if "text" in item:
                            text += str(item["text"])
                        elif "content" in item:
                            text += str(item["content"])

                prior_messages.append(text)

            else:
                prior_messages.append(str(content))

    prior = "\n".join(prior_messages)

    return prior + "\n" + question

def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Document]]:
    """
    Answer the given question with RAG; return the answer and the context documents.
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