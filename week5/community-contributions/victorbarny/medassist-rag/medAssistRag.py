import os
from pathlib import Path
from typing import List, Tuple, Dict
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from langchain_core.documents import Document

import gradio as gr
from litellm import completion
from tenacity import retry, wait_exponential

load_dotenv(override=True)

MODEL = "gpt-4.1-nano"
EMBEDDING_MODEL = "text-embedding-3-large"
KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge-base"
RETRIEVAL_K = 5

embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
llm = ChatOpenAI(model=MODEL, temperature=0.2, timeout=30)
vectorstore = None

class CritiqueResult(BaseModel):
    confidence: float = Field(description="Confidence score from 0.0 to 1.0 based on how well the context answers the question.")
    feedback: str = Field(description="Explanation of why the confidence score was given.")
    accuracy_check: str = Field(description="Check for any potential medical misinformation.")



def to_toon(docs: List[Document]) -> str:
    """
    Converts a list of LangChain Documents into a compact TOON-style pipe-separated format.
    """
    if not docs:
        return "No context available."
    
    header = "ID | Source | Content"
    rows = []
    for i, doc in enumerate(docs):
        source = Path(doc.metadata.get("source", "unknown")).name
        content = doc.page_content.replace("\n", " ").strip()[:500]
        rows.append(f"{i+1} | {source} | {content}")
    
    return f"{header}\n" + "\n".join(rows)


def ingest():
    """Load and index the knowledge base."""
    global vectorstore
    print("Starting ingestion...")
    loader = DirectoryLoader(
        str(KNOWLEDGE_BASE_DIR), 
        glob="**/*.md", 
        loader_cls=TextLoader, 
        loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    
    vectorstore = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings,
        persist_directory=None
    )
    print(f"Ingested {len(chunks)} chunks from {len(documents)} documents.")

def rewrite_query(question: str, history: List[Dict]) -> str:
    """Refine user question for medical search."""
    messages = [
        SystemMessage(content="You are a medical search specialist. Rewrite the user's question to be more specific and clinical for search. Respond ONLY with the query."),
        HumanMessage(content=f"Context history: {history}\nQuestion: {question}")
    ]
    return llm.invoke(messages).content

def retrieve(query: str) -> List[Document]:
    return vectorstore.similarity_search(query, k=RETRIEVAL_K)

@retry(wait=wait_exponential(multiplier=1, min=2, max=10))
def critique_answer(question: str, answer: str, context: str) -> CritiqueResult:
    """Self-critique loop to judge answer quality."""
    prompt = f"""
    Evaluate the following medical answer based on the provided context.
    Question: {question}
    Context (TOON format):
    {context}
    Answer: {answer}
    
    Provide a confidence score (0-1), feedback, and an accuracy check.
    """
    response = completion(
        model=f"openai/{MODEL}",
        messages=[{"role": "user", "content": prompt}],
        response_format=CritiqueResult
    )
    return CritiqueResult.model_validate_json(response.choices[0].message.content)

def answer_question(message: str, history: List[Dict]) -> Tuple[str, float, List[Document]]:
    """Main RAG pipeline logic."""
    query = rewrite_query(message, history)
    
    docs = retrieve(query)
    toon_context = to_toon(docs)
    
    system_prompt = f"""
    You are MedAssist, a medical knowledge worker. 
    Use the following Context (in TOON format) to answer the user accurately.
    If you don't know, say so. ALWAYS include a disclaimer that this is not professional medical advice.
    
    Context:
    {toon_context}
    """
    messages = [SystemMessage(content=system_prompt)] + convert_to_messages(history) + [HumanMessage(content=message)]
    response = llm.invoke(messages).content
    
    critique = critique_answer(message, response, toon_context)
    
    if critique.confidence < 0.6:
        print(f"Low confidence ({critique.confidence}). Re-retrieving with original query...")
        docs = retrieve(message)
        toon_context = to_toon(docs)
        system_prompt = f"RE-RETRIEVED CONTEXT:\n{toon_context}\n\n" + system_prompt
        messages = [SystemMessage(content=system_prompt)] + convert_to_messages(history) + [HumanMessage(content=message)]
        response = llm.invoke(messages).content
        critique = critique_answer(message, response, toon_context)
            
    return response, critique.confidence, docs



def format_ui_sources(docs: List[Document], confidence: float) -> str:
    res = f"### 📊 Confidence Score: `{confidence:.2f}/1.00`\n\n---\n### 📚 Retrieved Sources\n\n"
    for i, doc in enumerate(docs):
        src = Path(doc.metadata.get("source", "unknown")).name
        res += f"**[{i+1}] {src}**\n\n>{doc.page_content}\n\n"
    return res

def chat_interface_fn(message, history):
    """Event handler for Gradio UI."""
    internal_history = []
    for pair in history:
        internal_history.append({"role": "user", "content": pair[0]})
        internal_history.append({"role": "assistant", "content": pair[1]})
    
    answer, confidence, docs = answer_question(message, internal_history)
    sources_markdown = format_ui_sources(docs, confidence)
    
    history.append((message, answer))
    return "", history, sources_markdown


def run_app():
    ingest()
    
    with gr.Blocks(title="MedAssist RAG", theme=gr.themes.Soft()) as ui:
        gr.Markdown("# 🏥 MedAssist: Medical Knowledge Worker (Functional Version)\nAsk me about diseases, drugs, or first-aid procedures.")
        
        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(label="Conversation", height=600)
                msg = gr.Textbox(label="Your Question", placeholder="How to treat a minor burn?", show_label=False)
                clear = gr.Button("Clear")
            
            with gr.Column(scale=1):
                sources_panel = gr.Markdown("### 📊 Metrics & Sources\nRetrieved context will appear here.")
        
        msg.submit(chat_interface_fn, [msg, chatbot], [msg, chatbot, sources_panel])
        clear.click(lambda: (None, None, "Retrieved context will appear here."), None, [chatbot, msg, sources_panel])

    ui.launch(inbrowser=True)

if __name__ == "__main__":
    run_app()
