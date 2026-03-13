"""
Gmail Knowledge Worker
Loads sent emails from JSON, builds a Chroma vector store using OpenAI embeddings,
and provides a Gradio chat interface to query your sent emails.
"""

import json
from pathlib import Path
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import gradio as gr

load_dotenv(override=True)

# Configuration of the Gmail Knowledge Worker
MODEL = "gpt-4.1-nano"
EMAILS_FILE = Path(__file__).parent / "sent_emails.json"
DB_NAME = str(Path(__file__).parent / "chroma_db")
RETRIEVAL_K = 10

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vectorstore = None
llm = ChatOpenAI(temperature=0, model_name=MODEL)

SYSTEM_PROMPT = """
You are a helpful personal assistant with access to the user's sent Gmail emails.
Use the email context below to answer questions about past conversations, people contacted,
topics discussed, and any other information found in the emails.
If you don't know the answer from the emails, say so honestly.

Context:
{context}
"""

# Vector store builders to build the vector store from the emails

def load_emails() -> list[dict]:
    """Load emails from JSON file"""
    with open(EMAILS_FILE, 'r', encoding='utf-8') as f:
        emails = json.load(f)
    print(f"✓ Loaded {len(emails)} emails")
    return emails

def emails_to_documents(emails: list[dict]) -> list[Document]:
    """Convert emails to LangChain Document objects"""
    docs = []
    for email in emails:
        content = f"""
Date: {email.get('date', 'Unknown')}
To: {email.get('to', 'Unknown')}
Subject: {email.get('subject', 'No Subject')}

{email.get('body', '')}
        """.strip()

        metadata = {
            'id': email.get('id', ''),
            'subject': email.get('subject', ''),
            'to': email.get('to', ''),
            'date': email.get('date', ''),
        }
        docs.append(Document(page_content=content, metadata=metadata))

    print(f"✓ Converted {len(docs)} emails to documents")
    return docs

def build_vector_store(docs: list[Document]) -> Chroma:
    """Build and persist Chroma vector store from documents"""
    print("Building vector store... this may take a moment.")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    print(f"✓ Split into {len(chunks)} chunks")

    vs = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_NAME
    )
    print(f"✓ Vector store saved to {DB_NAME}")
    return vs

def get_vector_store() -> Chroma:
    """Load existing or build new vector store"""
    if Path(DB_NAME).exists():
        print("✓ Found existing vector store, loading...")
        return Chroma(persist_directory=DB_NAME, embedding_function=embeddings)
    else:
        print("No vector store found, building new one...")
        emails = load_emails()
        docs = emails_to_documents(emails)
        return build_vector_store(docs)

# RAG functions

def fetch_context(question: str) -> list[Document]:
    """Retrieve relevant context documents for a question"""
    retriever = vectorstore.as_retriever()
    return retriever.invoke(question, k=RETRIEVAL_K)

def combined_question(question: str, history: list[dict] = []) -> str:
    """Combine all the user's messages into a single string"""
    prior = "\n".join(m["content"] for m in history if m["role"] == "user")
    return prior + "\n" + question

def answer_question(question: str, history: list[dict] = []) -> str:
    """Answer the given question with RAG"""
    combined = combined_question(question, history)
    docs = fetch_context(combined)
    context = "\n\n".join(doc.page_content for doc in docs)
    system_prompt = SYSTEM_PROMPT.format(context=context)
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(history))
    messages.append(HumanMessage(content=question))
    response = llm.invoke(messages)
    return response.content

# Gradio UI to interact with the Gmail Knowledge Worker

def chat(message: str, history: list[dict]) -> str:
    """Gradio chat handler"""
    return answer_question(message, history)

def main():
    global vectorstore
    vectorstore = get_vector_store()
    print("✓ Gmail Knowledge Worker ready!")

    demo = gr.ChatInterface(
        fn=chat,
        type="messages",
        title="My Personal Gmail Knowledge Worker",
        description="Ask questions about your sent emails. Powered by GPT-4.1-nano + OpenAI embeddings.",
        examples=[
            "Who have I emailed about meetings?",
            "What projects have I discussed recently?",
            "Find emails where I mentioned invoices",
        ]
    )
    demo.launch()

if __name__ == '__main__':
    main()