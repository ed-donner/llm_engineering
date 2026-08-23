import os
# Avoid tokenizers fork warning when using HuggingFaceEmbeddings + Chroma
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv(override=True)

#### Embeddings (must match what was used in obsidian_ingest.py)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

#### Paths
SCRIPT_DIR = Path(__file__).resolve().parent
CHROMA_DB_PATH = str(SCRIPT_DIR / "chroma_db")
vectorstore = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

#### Local LLM (Ollama)
MODEL = "glm-4.7-flash"  # run: ollama pull glm-4.7-flash
OLLAMA_BASE_URL = "http://localhost:11434/v1"

ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key='ollama')
SYSTEM_PROMPT = """You are a helpful Dungeons & Dragons DM assistant. Answer using the context below when relevant. If the answer isn't in the context, say so.

Context:
{context}
"""


def get_context(question: str) -> str:
    docs = retriever.invoke(question)
    return "\n\n".join(doc.page_content for doc in docs)


def chat(question: str, history: list[dict]) -> tuple[str, list[dict]]:
    """RAG chat: retrieve context, call Ollama, return answer and updated history."""
    context = get_context(question)
    system_content = SYSTEM_PROMPT.format(context=context)
    messages = [{"role": "system", "content": system_content}]
    messages.extend(history)
    messages.append({"role": "user", "content": question})

    response = ollama.chat.completions.create(model=MODEL, messages=messages)
    # ollama returns a ChatResponse object: response.message.content
    answer = (response.choices[0].message.content or "") if response.choices[0].message else ""

    new_history = history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]
    return answer, new_history


def main() -> None:
    history: list[dict] = []
    print("Welcome to the Obsidian Chat assistant!")
    print("Ask me anything about the Obsidian vault.")
    print("Type 'exit' or 'quit' to end the session.")
    print("--------------------------------")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break
        answer, history = chat(user_input, history)
        print(f"Assistant: {answer}")
        print()


if __name__ == "__main__":
    main()
