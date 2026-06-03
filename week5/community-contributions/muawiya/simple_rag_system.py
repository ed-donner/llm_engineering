#!/usr/bin/env python3
"""
Simple All-in-One RAG System for Personal Data
Handles .docx files, creates sample CV, and provides interactive interface
"""

import os
import sys
from pathlib import Path

# Install required packages if not already installed
try:
    from langchain_community.vectorstores import Chroma
    from langchain.docstore.document import Document
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.document_loaders import PyPDFLoader
    from langchain.text_splitter import CharacterTextSplitter
except ImportError:
    print("Installing required packages...")
    os.system("pip install langchain-huggingface pypdf")
    from langchain_community.vectorstores import Chroma
    from langchain.docstore.document import Document
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.document_loaders import PyPDFLoader
    from langchain.text_splitter import CharacterTextSplitter

def create_sample_cv():
    """Create a sample CV text file"""
    sample_cv = """
    CURRICULUM VITAE - MUAWIYA
    
    PERSONAL INFORMATION
    Name: Muawiya
    Email: muawiya@example.com
    Phone: +1234567890
    Location: [Your Location]
    
    PROFESSIONAL SUMMARY
    Enthusiastic developer and student with a passion for technology and programming. 
    Currently learning Django framework and web development. Active participant in 
    the LLM engineering community and working on personal projects.
    
    EDUCATION
    - Currently pursuing studies in Computer Science/Programming
    - Learning Django web framework
    - Studying web development and programming concepts
    
    TECHNICAL SKILLS
    - Python Programming
    - Django Web Framework
    - Virtual Environment Management
    - Git and GitHub
    - Database Management with Django
    - Basic Web Development
    
    CURRENT PROJECTS
    - Learning Django through practical exercises
    - Building web applications
    - Working on LLM engineering projects
    - Contributing to community projects
    - Personal data management and RAG systems
    
    LEARNING GOALS
    - Master Django framework
    - Build full-stack web applications
    - Learn machine learning and AI
    - Contribute to open source projects
    - Develop expertise in modern web technologies
    
    INTERESTS
    - Web Development
    - Artificial Intelligence
    - Machine Learning
    - Open Source Software
    - Technology and Programming
    
    LANGUAGES
    - English
    - [Add other languages if applicable]
    
    CERTIFICATIONS
    - [Add any relevant certifications]
    
    REFERENCES
    Available upon request
    """
    
    # Create Personal directory if it doesn't exist
    personal_dir = Path("Personal")
    personal_dir.mkdir(exist_ok=True)
    
    # Create the sample CV file
    cv_file = personal_dir / "CV_Muawiya.txt"
    
    with open(cv_file, 'w', encoding='utf-8') as f:
        f.write(sample_cv.strip())
    
    print(f"✅ Created sample CV: {cv_file}")
    return cv_file

def load_documents():
    """Load all documents from Personal directory"""
    documents = []
    input_path = Path("Personal")
    
    # Supported file extensions
    text_extensions = {'.txt', '.md', '.log', '.csv', '.json'}
    pdf_extensions = {'.pdf'}
    
    print(f"🔍 Scanning directory: {input_path}")
    
    for file_path in input_path.rglob("*"):
        if file_path.is_file():
            file_ext = file_path.suffix.lower()
            
            try:
                if file_ext in text_extensions:
                    # Handle text files
                    with open(file_path, "r", encoding="utf-8", errors='ignore') as f:
                        content = f.read().strip()
                        if content and len(content) > 10:
                            documents.append(Document(
                                page_content=content,
                                metadata={"source": str(file_path.relative_to(input_path)), "type": "text"}
                            ))
                            print(f"  ✅ Loaded: {file_path.name} ({len(content)} chars)")
                            
                elif file_ext in pdf_extensions:
                    # Handle PDF files
                    try:
                        loader = PyPDFLoader(str(file_path))
                        pdf_docs = loader.load()
                        valid_docs = 0
                        for doc in pdf_docs:
                            if doc.page_content.strip() and len(doc.page_content.strip()) > 10:
                                doc.metadata["source"] = str(file_path.relative_to(input_path))
                                doc.metadata["type"] = "pdf"
                                documents.append(doc)
                                valid_docs += 1
                        if valid_docs > 0:
                            print(f"  ✅ Loaded PDF: {file_path.name} ({valid_docs} pages with content)")
                    except Exception as e:
                        print(f"  ⚠️  Skipped PDF: {file_path.name} (error: {e})")
                
            except Exception as e:
                print(f"  ❌ Error processing {file_path.name}: {e}")
    
    return documents

def create_rag_system():
    """Create the RAG system with all documents"""
    print("🚀 Creating RAG System")
    print("=" * 50)
    
    # Step 1: Create sample CV if it doesn't exist
    cv_file = Path("Personal/CV_Muawiya.txt")
    if not cv_file.exists():
        print("📝 Creating sample CV...")
        create_sample_cv()
    
    # Step 2: Load all documents
    documents = load_documents()
    print(f"\n📊 Loaded {len(documents)} documents")
    
    if len(documents) == 0:
        print("❌ No documents found! Creating sample document...")
        sample_content = "This is a sample document for testing the RAG system."
        documents.append(Document(
            page_content=sample_content,
            metadata={"source": "sample.txt", "type": "sample"}
        ))
    
    # Step 3: Load embedding model
    print("\n🤖 Loading embedding model...")
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Step 4: Split documents into chunks
    print("✂️  Splitting documents into chunks...")
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    print(f"📝 Created {len(chunks)} chunks")
    
    # Step 5: Create vectorstore
    print("🗄️  Creating vector database...")
    db_path = "chroma_failures_ds"
    vectorstore = Chroma.from_documents(documents=chunks, embedding=embedding_model, persist_directory=db_path)
    print(f"✅ Vectorstore created with {vectorstore._collection.count()} documents")
    
    return vectorstore

def search_documents(vectorstore, query, k=5):
    """Search documents with similarity scores - get more results for better filtering"""
    try:
        results = vectorstore.similarity_search_with_score(query, k=k)
        return results
    except Exception as e:
        print(f"❌ Error searching: {e}")
        return []

def display_results(results, query):
    """Display search results with relevance filtering"""
    print(f"\n🔍 Results for: '{query}'")
    print("=" * 60)
    
    if not results:
        print("❌ No results found.")
        return
    
    # Filter results by relevance (only show relevant ones)
    relevant_results = []
    irrelevant_results = []
    
    for doc, score in results:
        # Chroma uses cosine distance, so lower score = more similar
        # Convert to relevance score (0-1, where 1 is most relevant)
        # For cosine distance: 0 = identical, 2 = completely different
        relevance = 1 - (score / 2)  # Normalize to 0-1 range
        
        if relevance > 0.3:  # Show results with >30% relevance
            relevant_results.append((doc, score, relevance))
        else:
            irrelevant_results.append((doc, score, relevance))
    
    # Show relevant results
    if relevant_results:
        print(f"\n✅ Relevant Results ({len(relevant_results)} found):")
        print("-" * 50)
        
        # Group results by source to avoid duplicates
        seen_sources = set()
        unique_results = []
        
        for doc, score, relevance in relevant_results:
            source = doc.metadata.get('source', 'Unknown')
            if source not in seen_sources:
                seen_sources.add(source)
                unique_results.append((doc, score, relevance))
        
        for i, (doc, score, relevance) in enumerate(unique_results, 1):
            print(f"\n📄 Result {i} (Relevance: {relevance:.2f})")
            print(f"📁 Source: {doc.metadata.get('source', 'Unknown')}")
            print(f"📝 Type: {doc.metadata.get('type', 'Unknown')}")
            print("-" * 40)
            
            # Display content - show more content for better context
            content = doc.page_content.strip()
            if len(content) > 500:  # Show more content
                content = content[:500] + "..."
            
            lines = content.split('\n')
            for line in lines[:12]:  # Show more lines
                if line.strip():
                    print(f"  {line.strip()}")
            
            if len(lines) > 12:
                print(f"  ... ({len(lines) - 12} more lines)")
        
        # Show summary if there were duplicates
        if len(relevant_results) > len(unique_results):
            print(f"\n💡 Note: {len(relevant_results) - len(unique_results)} duplicate results from same sources were combined.")
    
    # Show summary of irrelevant results
    if irrelevant_results:
        print(f"\n⚠️  Low Relevance Results ({len(irrelevant_results)} filtered out):")
        print("-" * 50)
        print("These results had low similarity to your query and were filtered out.")
        
        for i, (doc, score, relevance) in enumerate(irrelevant_results[:2], 1):  # Show first 2
            source = doc.metadata.get('source', 'Unknown')
            print(f"  {i}. {source} (Relevance: {relevance:.2f})")
        
        if len(irrelevant_results) > 2:
            print(f"  ... and {len(irrelevant_results) - 2} more")
    
    # If no relevant results found
    if not relevant_results:
        print(f"\n❌ No relevant results found for '{query}'")
        print("💡 Your documents contain:")
        print("   • Personal CV information")
        print("   • Django commands and setup instructions")
        print("   • GitHub recovery codes")
        print("   • Various PDF documents")
        print("\n🔍 Try asking about:")
        print("   • Muawiya's personal information")
        print("   • Muawiya's skills and experience")
        print("   • Django project creation")
        print("   • Django commands")
        print("   • Virtual environment setup")

def interactive_query(vectorstore):
    """Interactive query interface"""
    print("\n🎯 Interactive Query Interface")
    print("=" * 50)
    print("💡 Example questions:")
    print("  • 'Who is Muawiya?'")
    print("  • 'What are Muawiya's skills?'")
    print("  • 'What is Muawiya's education?'")
    print("  • 'How do I create a Django project?'")
    print("  • 'What are the Django commands?'")
    print("  • 'quit' to exit")
    print("=" * 50)
    
    while True:
        try:
            query = input("\n❓ Ask a question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                print("⚠️  Please enter a question.")
                continue
            
            print(f"\n🔍 Searching for: '{query}'")
            results = search_documents(vectorstore, query, k=5)
            display_results(results, query)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main function - everything in one place"""
    print("🚀 Simple All-in-One RAG System")
    print("=" * 60)
    
    # Create the RAG system
    vectorstore = create_rag_system()
    
    print(f"\n🎉 RAG system is ready!")
    print(f"📁 Database location: chroma_failures_ds")
    
    # Start interactive interface
    interactive_query(vectorstore)

if __name__ == "__main__":
    main() 