import os
from pathlib import Path
from typing import List, Optional
import json
import tempfile
import shutil

from langchain_core.documents import Document
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.chains import ConversationalRetrievalChain


class DevOpsKnowledgeBase:
    def __init__(self, knowledge_base_path: str, embedding_model: str = "all-MiniLM-L6-v2"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.embedding_model_name = embedding_model
        self.embedding_model = None
        self.vectorstore = None
        self.documents = []
        self.chunks = []
        self.temp_db_dir = None

    def load_documents(self) -> List[Document]:
        self.documents = []

        if not self.knowledge_base_path.exists():
            raise ValueError(f"Knowledge base path does not exist: {self.knowledge_base_path}")

        supported_extensions = {'.yaml', '.yml', '.md', '.txt', '.json'}

        print(f"Loading documents from {self.knowledge_base_path}...")

        for file_path in self.knowledge_base_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().strip()

                    if content and len(content) > 50:
                        relative_path = file_path.relative_to(self.knowledge_base_path)
                        doc = Document(
                            page_content=content,
                            metadata={
                                "source": str(relative_path),
                                "file_type": file_path.suffix.lower(),
                                "path": str(file_path)
                            }
                        )
                        self.documents.append(doc)

                except Exception as e:
                    print(f"Skipped {file_path.name}: {str(e)}")

        print(f"Loaded {len(self.documents)} documents")
        return self.documents

    def chunk_documents(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
        if not self.documents:
            raise ValueError("No documents loaded. Call load_documents() first.")

        print(f"Splitting {len(self.documents)} documents into chunks...")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

        self.chunks = text_splitter.split_documents(self.documents)
        print(f"Created {len(self.chunks)} chunks")
        return self.chunks

    def initialize_embedding_model(self):
        print(f"Initializing embedding model: {self.embedding_model_name}...")
        self.embedding_model = HuggingFaceEmbeddings(model_name=self.embedding_model_name)
        print("Embedding model initialized")

    def create_vectorstore(self) -> Chroma:
        if not self.chunks:
            raise ValueError("No chunks available. Call chunk_documents() first.")

        if not self.embedding_model:
            raise ValueError("Embedding model not initialized. Call initialize_embedding_model() first.")

        print("Creating vector store...")

        if self.temp_db_dir:
            try:
                shutil.rmtree(self.temp_db_dir)
            except:
                pass

        self.temp_db_dir = tempfile.mkdtemp(prefix="devops_kb_")

        self.vectorstore = Chroma.from_documents(
            documents=self.chunks,
            embedding=self.embedding_model,
            persist_directory=self.temp_db_dir
        )

        doc_count = self.vectorstore._collection.count()
        print(f"Vector store created with {doc_count} documents")
        return self.vectorstore

    def initialize(self):
        print("Initializing DevOps Knowledge Base...")
        print("=" * 60)

        self.load_documents()
        self.chunk_documents()
        self.initialize_embedding_model()
        self.create_vectorstore()

        print("\nKnowledge base initialized successfully!")
        return self.vectorstore


class DevOpsAIAssistant:
    def __init__(self, knowledge_base_path: str, embedding_model: str = "all-MiniLM-L6-v2"):
        self.knowledge_base = DevOpsKnowledgeBase(knowledge_base_path, embedding_model)
        self.vectorstore = None
        self.conversation_chain = None
        self.memory = None
        self.llm = None

    def setup(self):
        print("Setting up DevOps AI Assistant...")

        self.vectorstore = self.knowledge_base.initialize()

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        print("Initializing OpenAI LLM...")
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.3,
            api_key=api_key
        )

        print("Setting up conversation memory...")
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key='answer'
        )

        print("Creating conversation chain...")
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})

        self.conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=self.memory,
            return_source_documents=True,
            verbose=False
        )

        print("DevOps AI Assistant ready!")
        return self

    def ask(self, question: str) -> dict:
        if not self.conversation_chain:
            raise ValueError("Assistant not initialized. Call setup() first.")

        result = self.conversation_chain.invoke({"question": question})

        response = {
            "answer": result.get('answer', ''),
            "sources": []
        }

        if result.get('source_documents'):
            for doc in result['source_documents']:
                response["sources"].append({
                    "content": doc.page_content[:300],
                    "source": doc.metadata.get('source', 'Unknown'),
                    "file_type": doc.metadata.get('file_type', 'Unknown')
                })

        return response

    def get_status(self) -> dict:
        if not self.vectorstore:
            return {"status": "not_initialized"}

        doc_count = self.vectorstore._collection.count()

        return {
            "status": "ready",
            "documents_loaded": len(self.knowledge_base.documents),
            "chunks_created": len(self.knowledge_base.chunks),
            "vectors_in_store": doc_count,
            "knowledge_base_path": str(self.knowledge_base.knowledge_base_path)
        }


def create_assistant(knowledge_base_path: str) -> DevOpsAIAssistant:
    assistant = DevOpsAIAssistant(knowledge_base_path)
    assistant.setup()
    return assistant
