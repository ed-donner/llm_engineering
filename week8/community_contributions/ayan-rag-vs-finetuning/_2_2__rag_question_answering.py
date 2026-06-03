from huggingface_hub import login
from dotenv import load_dotenv
import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from litellm import completion


DB_NAME = "chroma_langchain_db"
MODEL = "gpt-4.1-nano"


load_dotenv(override=True)
hf_token = os.getenv('HF_TOKEN')
login(token=hf_token)


SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant.
Your answer will be evaluated for accuracy, relevance and completeness, so make sure it only answers the question and fully answers it.
If you don't know the answer, say so.
For context, here are specific extracts from the Knowledge Base that might be directly relevant to the user's question:
{context}

With this context, please answer the user's question. Be accurate, relevant and complete.
"""


def make_rag_messages(question, chunks):
    
    context = "\n\n".join(f"Extract from {chunk.metadata['source']}:\n{chunk.page_content}" for chunk in chunks)
    system_prompt = SYSTEM_PROMPT.format(context=context)
    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "user", "content": question})
    return messages


embeddings = HuggingFaceEmbeddings(model_name="google/embeddinggemma-300m")


retriever = Chroma(
    collection_name="context_collection",
    embedding_function=embeddings,
    persist_directory=DB_NAME
).as_retriever()


def rag_answer(question):
    chunks = retriever.invoke(question)
    messages = make_rag_messages(question, chunks)
    response = completion(model=MODEL, messages=messages)
    return response.choices[0].message.content
