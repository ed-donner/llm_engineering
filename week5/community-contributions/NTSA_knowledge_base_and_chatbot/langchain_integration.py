#!/usr/bin/env python3
"""
LangChain Integration for NTSA Knowledge Base
Provides advanced document processing and conversational AI capabilities
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Optional imports with fallbacks
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from sklearn.manifold import TSNE
    from sklearn.decomposition import PCA
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# LangChain imports
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import Chroma
    from langchain.chains import ConversationalRetrievalChain
    from langchain.memory import ConversationBufferMemory
    from langchain.llms import OpenAI
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class LangChainKnowledgeBase:
    """Advanced knowledge base using LangChain for document processing and conversational AI"""
    
    def __init__(self, knowledge_base_dir: str = "ntsa_comprehensive_knowledge_base", 
                 vector_db_dir: str = "langchain_chroma_db"):
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.vector_db_dir = Path(vector_db_dir)
        self.documents = []
        self.vectorstore = None
        self.qa_chain = None
        self.memory = None
        
        # Initialize components
        self._setup_directories()
        self._load_documents()
        
    def _setup_directories(self):
        """Setup required directories"""
        self.vector_db_dir.mkdir(exist_ok=True)
        print(f"✅ Vector database directory: {self.vector_db_dir}")
        
    def _load_documents(self):
        """Load documents from the knowledge base"""
        print("📚 Loading documents from knowledge base...")
        
        if not self.knowledge_base_dir.exists():
            print(f"❌ Knowledge base directory not found: {self.knowledge_base_dir}")
            return
        
        documents = []
        for md_file in self.knowledge_base_dir.rglob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append({
                        'file': str(md_file),
                        'content': content,
                        'title': md_file.stem,
                        'category': md_file.parent.name
                    })
            except Exception as e:
                print(f"⚠️ Error reading {md_file}: {e}")
        
        self.documents = documents
        print(f"✅ Loaded {len(documents)} documents")
        
    def create_vector_store(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Create vector store from documents"""
        if not LANGCHAIN_AVAILABLE:
            print("❌ LangChain not available. Cannot create vector store.")
            return False
            
        if not self.documents:
            print("❌ No documents loaded. Cannot create vector store.")
            return False
        
        try:
            print("🔧 Creating vector store...")
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
            )
            
            texts = []
            metadatas = []
            
            for doc in self.documents:
                chunks = text_splitter.split_text(doc['content'])
                for chunk in chunks:
                    texts.append(chunk)
                    metadatas.append({
                        'source': doc['file'],
                        'title': doc['title'],
                        'category': doc['category']
                    })
            
            print(f"📄 Created {len(texts)} text chunks")
            
            # Create embeddings
            try:
                embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
                print("✅ HuggingFace embeddings loaded")
            except Exception as e:
                print(f"⚠️ HuggingFace embeddings failed: {e}")
                print("🔄 Using OpenAI embeddings as fallback...")
                from langchain.embeddings import OpenAIEmbeddings
                embeddings = OpenAIEmbeddings()
            
            # Create vector store
            self.vectorstore = Chroma.from_texts(
                texts=texts,
                embedding=embeddings,
                metadatas=metadatas,
                persist_directory=str(self.vector_db_dir)
            )
            
            # Persist the vector store
            self.vectorstore.persist()
            
            print(f"✅ Vector store created and persisted to {self.vector_db_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating vector store: {e}")
            return False
    
    def load_existing_vector_store(self):
        """Load existing vector store"""
        if not LANGCHAIN_AVAILABLE:
            print("❌ LangChain not available. Cannot load vector store.")
            return False
            
        try:
            print("📂 Loading existing vector store...")
            
            # Create embeddings
            try:
                embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
            except Exception as e:
                print(f"⚠️ HuggingFace embeddings failed: {e}")
                print("🔄 Using OpenAI embeddings as fallback...")
                from langchain.embeddings import OpenAIEmbeddings
                embeddings = OpenAIEmbeddings()
            
            # Load vector store
            self.vectorstore = Chroma(
                persist_directory=str(self.vector_db_dir),
                embedding_function=embeddings
            )
            
            print("✅ Vector store loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error loading vector store: {e}")
            return False
    
    def create_qa_chain(self, model_name: str = "gpt-3.5-turbo"):
        """Create question-answering chain"""
        if not LANGCHAIN_AVAILABLE:
            print("❌ LangChain not available. Cannot create QA chain.")
            return False
            
        if not self.vectorstore:
            print("❌ Vector store not available. Cannot create QA chain.")
            return False
        
        try:
            print(f"🔧 Creating QA chain with {model_name}...")
            
            # Initialize LLM
            llm = ChatOpenAI(
                model_name=model_name,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Create memory
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            # Create QA chain
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
                memory=self.memory,
                output_key="answer"
            )
            
            print("✅ QA chain created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error creating QA chain: {e}")
            return False
    
    def ask_question(self, question: str) -> str:
        """Ask a question to the knowledge base"""
        if not self.qa_chain:
            return "❌ QA chain not available. Please create it first."
        
        try:
            result = self.qa_chain({"question": question})
            return result["answer"]
        except Exception as e:
            return f"❌ Error answering question: {e}"
    
    def search_documents(self, query: str, k: int = 5) -> List[Dict]:
        """Search documents using vector similarity"""
        if not self.vectorstore:
            return []
        
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                }
                for doc, score in results
            ]
        except Exception as e:
            print(f"❌ Error searching documents: {e}")
            return []
    
    def visualize_embeddings(self, n_samples: int = 50, method: str = "tsne"):
        """Visualize document embeddings"""
        if not PLOTLY_AVAILABLE:
            print("❌ Plotly not available. Cannot create visualization.")
            return
        
        if not SKLEARN_AVAILABLE:
            print("❌ Scikit-learn not available. Cannot create visualization.")
            return
        
        if not NUMPY_AVAILABLE:
            print("❌ NumPy not available. Cannot create visualization.")
            return
        
        if not self.vectorstore:
            print("❌ Vector store not available. Cannot create visualization.")
            return
        
        try:
            print("📊 Visualizing embeddings...")
            
            # Get all documents and embeddings
            all_docs = self.vectorstore.get()
            
            if not all_docs or not all_docs.get('embeddings'):
                print("❌ No embeddings found in vector store.")
                return
            
            n_samples = min(n_samples, len(all_docs['ids']))
            embeddings_array = np.array(all_docs['embeddings'][:n_samples])
            texts = all_docs['documents'][:n_samples]
            
            if method == "tsne":
                # t-SNE dimensionality reduction
                tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, n_samples-1))
                embeddings_2d = tsne.fit_transform(embeddings_array)
            else:
                # PCA dimensionality reduction
                pca = PCA(n_components=2, random_state=42)
                embeddings_2d = pca.fit_transform(embeddings_array)
            
            # Create visualization
            fig = go.Figure()
            
            # Add scatter plot
            fig.add_trace(go.Scatter(
                x=embeddings_2d[:, 0],
                y=embeddings_2d[:, 1],
                mode='markers',
                marker=dict(
                    size=8,
                    color=range(n_samples),
                    colorscale='Viridis',
                    showscale=True
                ),
                text=[text[:100] + "..." if len(text) > 100 else text for text in texts],
                hovertemplate='<b>%{text}</b><br>X: %{x}<br>Y: %{y}<extra></extra>'
            ))
            
            fig.update_layout(
                title=f"Document Embeddings Visualization ({method.upper()})",
                xaxis_title="Dimension 1",
                yaxis_title="Dimension 2",
                showlegend=False
            )
            
            # Save and show
            fig.write_html("embeddings_visualization.html")
            fig.show()
            
            print("✅ Embeddings visualization created and saved as 'embeddings_visualization.html'")
            
        except Exception as e:
            print(f"❌ Error creating visualization: {e}")
            print("💡 This might be due to numpy compatibility issues.")
            print("💡 Try using OpenAI embeddings instead of HuggingFace embeddings.")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        stats = {
            "total_documents": len(self.documents),
            "vector_store_available": self.vectorstore is not None,
            "qa_chain_available": self.qa_chain is not None,
            "categories": {}
        }
        
        # Count documents by category
        for doc in self.documents:
            category = doc.get('category', 'unknown')
            if category not in stats['categories']:
                stats['categories'][category] = 0
            stats['categories'][category] += 1
        
        return stats
    
    def reset_memory(self):
        """Reset conversation memory"""
        if self.memory:
            self.memory.clear()
            print("✅ Conversation memory cleared")


def main():
    """Main function to demonstrate the knowledge base"""
    print("🚀 NTSA LangChain Knowledge Base")
    print("=" * 50)
    
    # Initialize knowledge base
    kb = LangChainKnowledgeBase()
    
    # Create vector store
    if kb.create_vector_store():
        print("✅ Vector store created successfully")
        
        # Create QA chain
        if kb.create_qa_chain():
            print("✅ QA chain created successfully")
            
            # Test the system
            test_questions = [
                "What is NTSA?",
                "How do I apply for a driving license?",
                "What services does NTSA provide?"
            ]
            
            print("\n🤖 Testing QA system:")
            for question in test_questions:
                print(f"\nQ: {question}")
                answer = kb.ask_question(question)
                print(f"A: {answer[:200]}{'...' if len(answer) > 200 else ''}")
            
            # Show statistics
            stats = kb.get_statistics()
            print(f"\n📊 Knowledge Base Statistics:")
            print(f"Total documents: {stats['total_documents']}")
            print(f"Categories: {stats['categories']}")
            
        else:
            print("❌ Failed to create QA chain")
    else:
        print("❌ Failed to create vector store")


if __name__ == "__main__":
    main()