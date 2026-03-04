"""
ULTRA DUMMIE DESCRIPTION
------------------------
What this file does:
- It is the RAG question-answering "engine".
- It searches context in vector_db.
- It injects that context into a prompt.
- It calls Ollama (llama3.1:8b) to answer.

Internal steps:
1) Loads environment and configures:
   - Chat model: Ollama llama3.1:8b
   - Embeddings: HuggingFace all-MiniLM-L6-v2
2) Opens Chroma (vector_db) and creates a retriever with K documents.
3) For each question:
   - combines user history + current question for retrieval,
   - retrieves similar documents,
   - builds context,
   - invokes the LLM with system prompt + history + question.
4) Returns answer and used documents.
5) If you run this file directly, it opens a terminal chat (CLI).

Key logic:
- Retrieval searches in the vector database.
- Generation writes the final answer using retrieved context.
- During the same session it keeps history in RAM.
"""

from pathlib import Path  # Imports Path to build robust paths.
from langchain_ollama import ChatOllama  # Imports local chat model from Ollama.
from langchain_huggingface import HuggingFaceEmbeddings  # Imports free HuggingFace embeddings for semantic retrieval.
from langchain_chroma import Chroma  # Imports Chroma vector store for semantic retrieval.
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages  # Imports message types and history converter.
from langchain_core.documents import Document  # Imports Document type for context typing.

from dotenv import load_dotenv  # Imports function to load environment variables from .env.


load_dotenv(override=True)  # Loads .env variables and allows overwriting existing environment variables.

MODEL = "llama3.1:8b"  # Defines local chat model served by Ollama.
#EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Defines free HuggingFace embedding model.
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

DB_NAME = str(Path(__file__).parent.parent / "vector_db")  # Builds path for persisted vector database.
DEBUG = True  # Enables or disables debug logs to trace flow.

embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)  # Initializes HuggingFace embedding model.
RETRIEVAL_K = 5  # Defines how many documents to retrieve as context.

SYSTEM_PROMPT = """  # Defines base system prompt with assistant instructions.
You are a strict retrieval-grounded assistant for Insurellm.

Rules you must follow:
1. Use ONLY the provided CONTEXT to answer.
2. Do NOT use prior knowledge, assumptions, or guesses.
3. If the answer is not explicitly supported by the CONTEXT, say exactly:
   "I don't have enough information in the knowledge base to answer that."
4. Never invent names, roles, products, numbers, dates, or facts.
5. If the user asks for people, list only names that appear exactly in the CONTEXT.
6. When possible, cite the source filename(s) from the context metadata.
7. Keep answers concise, factual, and grounded in the retrieved text.

CONTEXT:
{context}

"""  # Closes multiline system prompt string.

vectorstore = Chroma(persist_directory=DB_NAME, embedding_function=embeddings)  # Opens existing vector store with embedding function.
retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K})  # Creates retriever fixing how many documents to return per query.
llm = ChatOllama(temperature=0, model=MODEL)  # Initializes local Ollama chat model with more deterministic output.


def dbg(message):  # Defines helper to print traces only when DEBUG is active.
    if DEBUG:  # Checks debug flag.
        print(f"[ANSWER] {message}")  # Prints log with module prefix.


def fetch_context(question: str) -> list[Document]:  # Defines function to retrieve relevant documents for a question.
    """  # Opens function docstring.
    Retrieve relevant context documents for a question.  # Describes function purpose.
    """  # Closes function docstring.
    dbg(f"fetch_context() len(question)={len(question)}")  # Traces query length for retrieval.
    docs = retriever.invoke(question)  # Executes semantic retrieval using retriever configured `k`.
    dbg(f"Docs retrieved: {len(docs)}")  # Traces number of retrieved documents.
    for i, doc in enumerate(docs, start=1):  # Iterates documents to trace relevant metadata.
        dbg(f"Doc {i}: source={doc.metadata.get('source')} doc_type={doc.metadata.get('doc_type')}")  # Traces each doc source and type.
        dbg(f"Doc {i} full chunk content:\n{doc.page_content}")  # Prints full retrieved chunk content for inspection.
    return docs  # Returns retrieved documents list.


def combined_question(question: str, history: list[dict] = []) -> str:  # Defines function to combine history and current question.
    """  # Opens function docstring.
    Combine all the user's messages into a single string.  # Describes that it merges user messages.
    """  # Closes function docstring.
    prior = "\n".join(m["content"] for m in history if m["role"] == "user")  # Concatenates only previous user messages.
    combined = prior + "\n" + question  # Composes expanded query for retrieval.
    dbg(f"History received: {len(history)} messages | combined len={len(combined)}")  # Traces history size and final query length.
    return combined  # Returns previous user history plus current question.


def answer_question(  # Defines main RAG answer function.
    question: str,  # Receives current user question.
    history: list[dict] = [],  # Receives optional conversation history.
    model_name: str | None = None,  # Receives optional model override for generation.
) -> tuple[str, list[Document]]:  # Returns answer text and retrieved documents.
    """  # Opens function docstring.
    Answer the given question with RAG; return the answer and the context documents.  # Describes output: answer and context docs.
    """  # Closes function docstring.
    dbg(f"User question: {question}")  # Traces incoming question text.
    combined = combined_question(question, history)  # Builds query enriched with history.
    docs = fetch_context(combined)  # Retrieves relevant documents from vector store.
    context = "\n\n".join(doc.page_content for doc in docs)  # Merges document content into one context block.
    dbg(f"Context chars: {len(context)}")  # Traces context size for prompt.
    system_prompt = SYSTEM_PROMPT.format(context=context)  # Injects real context into system prompt.
    messages = [SystemMessage(content=system_prompt)]  # Creates messages list starting with system instructions.
    messages.extend(convert_to_messages(history))  # Adds previous history converted to message format.
    messages.append(HumanMessage(content=question))  # Adds current user question at the end.
    dbg(f"Messages sent to LLM: {len(messages)}")  # Traces number of messages sent to model.
    dbg("Invoking LLM...")  # Traces start of model call.
    selected_model = model_name or MODEL  # Resolves effective model (override or default).
    dbg(f"Generation model selected: {selected_model}")  # Traces selected generation model.
    selected_llm = llm if selected_model == MODEL else ChatOllama(temperature=0, model=selected_model)  # Reuses default LLM or builds override model client.
    response = selected_llm.invoke(messages)  # Invokes selected model with all prepared messages.
    dbg("Response received from LLM")  # Traces end of model call.
    return response.content, docs  # Returns answer text and used context documents.


def run_cli_chat():  # Defines terminal interactive mode to use RAG without web UI.
    history = []  # Initializes empty history to keep context between questions.
    dbg(f"Initializing CLI with MODEL={MODEL}, EMBEDDING_MODEL={EMBEDDING_MODEL}, RETRIEVAL_K={RETRIEVAL_K}")  # Traces startup configuration.
    print("RAG CLI ready. Type your question (or 'exit' to quit).")  # Shows initial usage message.
    while True:  # Starts continuous conversation loop.
        question = input("\nYour question: ").strip()  # Reads user question from terminal.
        if question.lower() in {"exit", "quit"}:  # Checks if user wants to end session.
            print("Session finished.")  # Shows close confirmation.
            break  # Exits loop and ends program.
        if not question:  # Checks whether user submitted empty text.
            print("Please type a valid question.")  # Informs that a real question is required.
            continue  # Returns to loop start without calling model.
        answer, docs = answer_question(question, history)  # Runs RAG with current question and current history.
        print(f"\nAnswer:\n{answer}")  # Prints generated model answer.
        print(f"\nRetrieved context: {len(docs)} document(s).")  # Prints how many documents were retrieved.
        history.append({"role": "user", "content": question})  # Saves user turn in history.
        history.append({"role": "assistant", "content": answer})  # Saves assistant turn in history.
        dbg(f"History in memory: {len(history)} messages")  # Traces current conversational memory size.


if __name__ == "__main__":  # Runs CLI mode when this file is executed directly.
    run_cli_chat()  # Launches terminal interactive chat.
