#!/usr/bin/env python3
"""
Knowledge Worker with Document Upload and Google Drive Integration

This script creates a knowledge worker that:
1. Allows users to upload documents through a Gradio UI
2. Integrates with Google Drive to access documents
3. Uses Chroma vector database for efficient document retrieval
4. Implements RAG (Retrieval Augmented Generation) for accurate responses

The system updates its context dynamically when new documents are uploaded.
"""

import os
import glob
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import gradio as gr

# LangChain imports
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma

# Visualization imports
import numpy as np
from sklearn.manifold import TSNE
import plotly.graph_objects as go

# Removed Google Drive API imports

# Additional document loaders
try:
    from langchain_community.document_loaders import Docx2txtLoader, UnstructuredExcelLoader
except ImportError:
    print("Warning: Some document loaders not available. PDF and text files will still work.")
    Docx2txtLoader = None
    UnstructuredExcelLoader = None

# Configuration
MODEL = "gpt-4o-mini"  # Using a cost-effective model
DB_NAME = "knowledge_worker_db"
UPLOAD_FOLDER = "uploaded_documents"

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load environment variables
load_dotenv(override=True)
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'your-key-if-not-using-env')

# Removed Google Drive credentials configuration

# Use a simple text splitter approach
class SimpleTextSplitter:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_documents(self, documents):
        chunks = []
        for doc in documents:
            text = doc.page_content
            start = 0
            while start < len(text):
                end = start + self.chunk_size
                chunk_text = text[start:end]
                chunk_doc = Document(page_content=chunk_text, metadata=doc.metadata.copy())
                chunks.append(chunk_doc)
                start = end - self.chunk_overlap
        return chunks

CharacterTextSplitter = SimpleTextSplitter

# Try different import paths for memory and chains
try:
    from langchain.memory import ConversationBufferMemory
    from langchain.chains import ConversationalRetrievalChain
except ImportError:
    try:
        from langchain_core.memory import ConversationBufferMemory
        from langchain_core.chains import ConversationalRetrievalChain
    except ImportError:
        try:
            from langchain_community.memory import ConversationBufferMemory
            from langchain_community.chains import ConversationalRetrievalChain
        except ImportError:
            print("Warning: Memory and chains modules not found. Creating simple alternatives.")
            # Create simple alternatives
            class ConversationBufferMemory:
                def __init__(self, memory_key='chat_history', return_messages=True):
                    self.memory_key = memory_key
                    self.return_messages = return_messages
                    self.chat_memory = []
                
                def save_context(self, inputs, outputs):
                    self.chat_memory.append((inputs, outputs))
                
                def load_memory_variables(self, inputs):
                    return {self.memory_key: self.chat_memory}
            
            class ConversationalRetrievalChain:
                def __init__(self, llm, retriever, memory):
                    self.llm = llm
                    self.retriever = retriever
                    self.memory = memory
                
                def invoke(self, inputs):
                    question = inputs.get("question", "")
                    # Simple implementation - just return a basic response
                    return {"answer": f"I received your question: {question}. This is a simplified response."}

# Removed Google Drive Integration Functions

# Document Processing Functions
def get_loader_for_file(file_path):
    """
    Get the appropriate document loader based on file extension
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        return PyPDFLoader(file_path)
    elif file_extension in ['.docx', '.doc'] and Docx2txtLoader:
        return Docx2txtLoader(file_path)
    elif file_extension in ['.xlsx', '.xls'] and UnstructuredExcelLoader:
        return UnstructuredExcelLoader(file_path)
    elif file_extension in ['.txt', '.md']:
        return TextLoader(file_path, encoding='utf-8')
    else:
        # Default to text loader for unknown types
        try:
            return TextLoader(file_path, encoding='utf-8')
        except:
            return None

def load_document(file_path):
    """
    Load a document using the appropriate loader
    """
    loader = get_loader_for_file(file_path)
    if loader:
        try:
            return loader.load()
        except Exception as e:
            print(f"Error loading document {file_path}: {e}")
    return []

def process_documents(documents):
    """
    Split documents into chunks for embedding
    """
    text_splitter = CharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    return chunks

# Knowledge Base Class
class KnowledgeBase:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = None
        self.initialize_vectorstore()
    
    def initialize_vectorstore(self):
        """
        Initialize the vector store, loading from disk if it exists
        """
        if os.path.exists(self.db_name):
            self.vectorstore = Chroma(persist_directory=self.db_name, embedding_function=self.embeddings)
            print(f"Loaded existing vector store with {self.vectorstore._collection.count()} documents")
        else:
            # Create empty vectorstore
            self.vectorstore = Chroma(persist_directory=self.db_name, embedding_function=self.embeddings)
            print("Created new vector store")
    
    def add_documents(self, documents):
        """
        Process and add documents to the vector store
        """
        if not documents:
            return False
        
        chunks = process_documents(documents)
        if not chunks:
            return False
        
        # Add to existing vectorstore
        self.vectorstore.add_documents(chunks)
        print(f"Added {len(chunks)} chunks to vector store")
        return True
    
    def get_retriever(self, k=4):
        """
        Get a retriever for the vector store
        """
        return self.vectorstore.as_retriever(search_kwargs={"k": k})
    
    def visualize_vectors(self):
        """
        Create a 3D visualization of the vector store
        """
        try:
            collection = self.vectorstore._collection
            result = collection.get(include=['embeddings', 'documents', 'metadatas'])
            
            if result['embeddings'] is None or len(result['embeddings']) == 0:
                print("No embeddings found in vector store")
                return None
            
            vectors = np.array(result['embeddings'])
            documents = result['documents']
            metadatas = result['metadatas']
            
            if len(vectors) < 2:
                print("Not enough vectors for visualization (need at least 2)")
                return None
            
            # Get source info for coloring
            sources = [metadata.get('source', 'unknown') for metadata in metadatas]
            unique_sources = list(set(sources))
            colors = [['blue', 'green', 'red', 'orange', 'purple', 'cyan'][unique_sources.index(s) % 6] for s in sources]
            
            # Reduce dimensions for visualization
            # Adjust perplexity based on number of samples
            n_samples = len(vectors)
            perplexity = min(30, max(1, n_samples - 1))
            
            tsne = TSNE(n_components=3, random_state=42, perplexity=perplexity)
            reduced_vectors = tsne.fit_transform(vectors)
            
            # Create the 3D scatter plot
            fig = go.Figure(data=[go.Scatter3d(
                x=reduced_vectors[:, 0],
                y=reduced_vectors[:, 1],
                z=reduced_vectors[:, 2],
                mode='markers',
                marker=dict(size=5, color=colors, opacity=0.8),
                text=[f"Source: {s}<br>Text: {d[:100]}..." for s, d in zip(sources, documents)],
                hoverinfo='text'
            )])
            
            fig.update_layout(
                title='3D Vector Store Visualization',
                scene=dict(xaxis_title='x', yaxis_title='y', zaxis_title='z'),
                width=900,
                height=700,
                margin=dict(r=20, b=10, l=10, t=40)
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating visualization: {e}")
            return None

# Simple fallback chain implementation
class SimpleConversationalChain:
    def __init__(self, llm, retriever, memory):
        self.llm = llm
        self.retriever = retriever
        self.memory = memory
    
    def invoke(self, inputs):
        question = inputs.get("question", "")
        # Get relevant documents - try different methods
        try:
            docs = self.retriever.get_relevant_documents(question)
        except AttributeError:
            try:
                docs = self.retriever.invoke(question)
            except:
                docs = []
        
        context = "\n".join([doc.page_content for doc in docs[:3]]) if docs else "No relevant context found."
        
        # Create a simple prompt
        prompt = f"""Based on the following context, answer the question:

Context: {context}

Question: {question}

Answer:"""
        
        # Get response from LLM
        response = self.llm.invoke(prompt)
        return {"answer": response.content if hasattr(response, 'content') else str(response)}

# Chat System Class
class ChatSystem:
    def __init__(self, knowledge_base, model_name=MODEL):
        self.knowledge_base = knowledge_base
        self.model_name = model_name
        self.llm = ChatOpenAI(temperature=0.7, model_name=self.model_name)
        self.memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
        self.conversation_chain = self._create_conversation_chain()
    
    def _create_conversation_chain(self):
        """
        Create a new conversation chain with the current retriever
        """
        retriever = self.knowledge_base.get_retriever()
        # Skip the problematic ConversationalRetrievalChain and use simple implementation
        print("Using simple conversational chain implementation")
        return SimpleConversationalChain(self.llm, retriever, self.memory)
    
    def reset_conversation(self):
        """
        Reset the conversation memory and chain
        """
        self.memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
        self.conversation_chain = self._create_conversation_chain()
        return "Conversation has been reset."
    
    def chat(self, question, history):
        """
        Process a question and return the answer
        """
        if not question.strip():
            return "Please ask a question."
        
        result = self.conversation_chain.invoke({"question": question})
        return result["answer"]
    
    def update_knowledge_base(self):
        """
        Update the conversation chain with the latest knowledge base
        """
        self.conversation_chain = self._create_conversation_chain()

# UI Functions
def handle_file_upload(files):
    """
    Process uploaded files and add them to the knowledge base
    """
    if not files:
        return "No files uploaded."
    
    documents = []
    for file in files:
        try:
            docs = load_document(file.name)
            if docs:
                # Add upload source metadata
                for doc in docs:
                    doc.metadata['source'] = 'upload'
                    doc.metadata['filename'] = os.path.basename(file.name)
                documents.extend(docs)
        except Exception as e:
            print(f"Error processing file {file.name}: {e}")
    
    if documents:
        success = kb.add_documents(documents)
        if success:
            # Update the chat system with new knowledge
            chat_system.update_knowledge_base()
            return f"Successfully processed {len(documents)} documents."
    
    return "No documents could be processed. Please check file formats."

def create_ui():
    """
    Create the Gradio UI
    """
    with gr.Blocks(theme=gr.themes.Soft()) as app:
        gr.Markdown("""
        # Knowledge Worker
        Upload documents or ask questions about your knowledge base.
        """)
        
        with gr.Tabs():
            with gr.TabItem("Chat"):
                chatbot = gr.ChatInterface(
                    chat_system.chat,
                    chatbot=gr.Chatbot(height=500, type="messages"),
                    textbox=gr.Textbox(placeholder="Ask a question about your documents...", container=False),
                    title="Knowledge Worker Chat",
                    type="messages"
                )
                reset_btn = gr.Button("Reset Conversation")
                reset_btn.click(chat_system.reset_conversation, inputs=None, outputs=gr.Textbox())
                
            with gr.TabItem("Upload Documents"):
                with gr.Column():
                    file_output = gr.Textbox(label="Upload Status")
                    upload_button = gr.UploadButton(
                        "Click to Upload Files",
                        file_types=[".pdf", ".docx", ".txt", ".md", ".xlsx"],
                        file_count="multiple"
                    )
                    upload_button.upload(handle_file_upload, upload_button, file_output)
            
            with gr.TabItem("Visualize Knowledge"):
                visualize_btn = gr.Button("Generate Vector Visualization")
                plot_output = gr.Plot(label="Vector Space Visualization")
                visualize_btn.click(kb.visualize_vectors, inputs=None, outputs=plot_output)
                
    return app

def main():
    """
    Main function to initialize and run the knowledge worker
    """
    global kb, chat_system
    
    print("=" * 60)
    print("Initializing Knowledge Worker...")
    print("=" * 60)
    
    try:
        # Initialize the knowledge base
        print("Setting up vector database...")
        kb = KnowledgeBase(DB_NAME)
        print("Vector database initialized successfully")
        
        # Google Drive integration removed
        
        # Initialize the chat system
        print("\nSetting up chat system...")
        chat_system = ChatSystem(kb)
        print("Chat system initialized successfully")
        
        # Launch the Gradio app
        print("\nLaunching Gradio interface...")
        print("=" * 60)
        print("The web interface will open in your browser")
        print("You can also access it at the URL shown below")
        print("=" * 60)
        
        app = create_ui()
        app.launch(inbrowser=True)
        
    except Exception as e:
        print(f"Error initializing Knowledge Worker: {e}")
        print("Please check your configuration and try again.")
        return

if __name__ == "__main__":
    main()
