import os
import glob
from langchain_classic.schema import HumanMessage, SystemMessage
from langchain_core.vectorstores import VectorStoreRetriever
import tiktoken
import numpy as np
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter 

# pip install --upgrade --force-reinstall --no-cache-dir langchain-openai langchain-chroma langchain-huggingface langchain-community plotly scikit-learn tiktoken python-dotenv
# price is a factor for our company, so we're going to use a low cost model
load_dotenv(override=True)
MODEL = "gpt-4.1-nano"
# MODEL = "gpt-oss-1.3b-8k"
db_name = "vector_db_attorney"
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

vectorstore: Chroma = None
OPEN_ROUTER_BASE_URL = os.getenv('OPEN_ROUTER_BASE_URL')

SYSTEM_PROMPT_TEMPLATE = """
You are a knowledgeable, friendly assistant representing the company Attorneyllm.
You are chatting with a user about Attorneyllm providing legal action to user about marraige.
If relevant, use the given context to answer any question.
If you don't know the answer, say so.
Context:
{context}
""" 
llm = ChatOpenAI(
    temperature=0,
    model_name=MODEL,
    base_url=OPEN_ROUTER_BASE_URL,
    api_key=OPENAI_API_KEY
)
def setup_env_and_model():
    
    global llm
    # Initialize LLM
    

    print(OPEN_ROUTER_BASE_URL, '  ---  ', OPENAI_API_KEY)
  
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key:
        print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
    else:
        print("OpenAI API Key not set")
        
def load_and_process_documents():
    # Load in everything in the knowledgebase using LangChain's loaders

    folders = glob.glob("llm-marriage-attorney-knowledge-base/*")

    documents = []
    for folder in folders:
        doc_type = os.path.basename(folder)
        loader = DirectoryLoader(folder, glob="**/*.md", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
        folder_docs = loader.load()
        for doc in folder_docs:
            doc.metadata["doc_type"] = doc_type
            documents.append(doc)

    print(f"Loaded {len(documents)} documents")
    return documents
    
def divide_into_chunks(documents):
    # Divide into chunks using the RecursiveCharacterTextSplitter

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)

    print(f"Divided into {len(chunks)} chunks")
    print(f"First chunk:\n\n{chunks[0]}")
    return chunks


def store_in_vector_db(): 
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    global vectorstore 

    if os.path.exists(db_name):
        vectorstore = Chroma(persist_directory=db_name, embedding_function=embeddings)
        return
        # Chroma(persist_directory=db_name, embedding_function=embeddings).delete_collection()
    documents = load_and_process_documents()
    chunks = divide_into_chunks(documents)
    vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=db_name)
    print(f"Vectorstore created with {vectorstore._collection.count()} documents")
    
# def ask(question: str, history):
#     global vectorstore
#     retriever= vectorstore.as_retriever()
#     docs = retriever.invoke(question)
#     context = "\n\n".join(doc.page_content for doc in docs)
#     system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)
#     llm = ChatOpenAI(temperature=0, model_name=MODEL, base_url=OPEN_ROUTER_BASE_URL, api_key=OPENAI_API_KEY)
#     response = llm([SystemMessage(content=system_prompt), HumanMessage(content=question)])
#     return response.content

def ask(question: str, history=None):
    global vectorstore
    
    # Get retriever
    retriever: VectorStoreRetriever = vectorstore.as_retriever()
    
    # Correct sync method for Chroma retriever
    docs = retriever.invoke(question)
    
    # Build context from retrieved docs
    context = "\n\n".join(doc.page_content for doc in docs)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

    global llm
    # Run LLM synchronously
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=question)])
    return response.content
 
# -----------------------
# GRADIO UI
# -----------------------

import gradio as gr

def start():

    setup_env_and_model() 

    store_in_vector_db()
   
    # Create a simple Gradio interface to ask questions
    print("Launching Gradio interface...")
    demo = gr.Interface(
        fn=ask,
        inputs=gr.Textbox(
            label="Ask about marriage legal cases",
            placeholder="Example: Why was Johnson vs Johnson divorce lost?",
            lines=10
        ),
        outputs=gr.Textbox(label="AI Legal Assistant", lines=10),
        title="Marriage Attorney Legal Assistant",
        description="Ask questions about divorce, annulment, custody, and legal case outcomes."
    )
    demo.launch(inbrowser=True)
    # demo.launch()
    print("Gradio UI launched")



start()