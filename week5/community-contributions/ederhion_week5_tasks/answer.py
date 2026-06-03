# answer.py
import os
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.documents import Document

from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

from dotenv import load_dotenv

# Import constants
from config import DB_NAME, DEVICE, LLM_MODEL, EMBEDDING_MODEL, RERANKER_MODEL, SYSTEM_PROMPT

load_dotenv(override=True)
API_KEY = os.getenv("OPENROUTER_API_KEY")

# 1. Initialize the local Metal Performance Shaders (MPS) embedding model
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={'device': DEVICE},   
    encode_kwargs={'normalize_embeddings': True}
)

# 2. Initialize the local cross-encoder reranker
reranker_model = HuggingFaceCrossEncoder(
    model_name=RERANKER_MODEL,
    model_kwargs={'device': DEVICE }
)

# 3. Setup the Chroma vector store
vectorstore = Chroma(persist_directory=DB_NAME, embedding_function=embeddings)

# 4. Create the two-stage retrieval pipeline
base_retriever = vectorstore.as_retriever(search_kwargs={"k": 30})

compressor = CrossEncoderReranker(model=reranker_model, top_n=5)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor, 
    base_retriever=base_retriever
)

# Configure ChatOpenAI to route through OpenRouter
llm = ChatOpenAI(
    model_name=LLM_MODEL,
    temperature=0,
    openai_api_key=API_KEY,
    openai_api_base="https://openrouter.ai/api/v1",
)

def rewrite_query(question: str, history: list[dict] = []) -> str:
    """
    Use the LLM to rewrite the conversational question into a highly specific search query.
    """
    if not history:
        return question
        
    prior_conversation = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    
    rewrite_prompt = f"""
    Given the following conversation history and a new user question, 
    rephrase the new question to be a standalone search query optimized for querying a technical database manual.
    
    Conversation History:
    {prior_conversation}
    
    New Question: {question}
    
    Standalone Query:"""
    
    response = llm.invoke([HumanMessage(content=rewrite_prompt)])
    return response.content.strip()

def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Document]]:
    """
    Answer the given question with advanced RAG; return the answer and the context documents.
    """
    # Step 1: Rewrite the query for better search accuracy
    optimized_query = rewrite_query(question, history)
    print(f"Optimized Search Query: {optimized_query}")
    
    # Step 2: Retrieve and Rerank the chunks
    docs = compression_retriever.invoke(optimized_query)
    
    # Step 3: Format context and generate the final answer
    context = "\n\n".join(doc.page_content for doc in docs)
    system_prompt_formatted = SYSTEM_PROMPT.format(context=context)
    
    messages = [SystemMessage(content=system_prompt_formatted)]
    
    # Append conversation history
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(SystemMessage(content=msg["content"]))
            
    messages.append(HumanMessage(content=question))
    
    response = llm.invoke(messages)
    return response.content, docs