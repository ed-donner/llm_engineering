import os
from dotenv import load_dotenv
import gradio as gr

from llm.utils import getKnowledgeDoc, doc2chunk, text2embedding, visualizeVector
from llm import chat


def setEnv():
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


def genChatTemplate(vector_store):
    def gradio_chat_fn(message, history):
        answer = chat(message, vector_store)
        return answer
    return gradio_chat_fn


def main():
    setEnv()
    documents = getKnowledgeDoc()
    chunks = doc2chunk(documents, chunk_size=1000, overlap=200)
    vector_store = text2embedding(chunks)
    print(
        f"VectorStore created with {vector_store._collection.count()} documents")
    # visualizeVector(vector_store)
    view = gr.ChatInterface(
        genChatTemplate(vector_store), type="messages").launch(inbrowser=True)


if __name__ == "__main__":
    main()
