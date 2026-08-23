#!/usr/bin/env python3
"""
Working NTSA Chatbot - Self-contained version
No external dependencies that cause numpy issues
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Load environment variables
load_dotenv()

class WorkingChatbot:
    """Simple working chatbot that uses the knowledge base directly"""
    
    def __init__(self, knowledge_base_dir: str = "ntsa_comprehensive_knowledge_base"):
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.documents = []
        self.conversation_history = []
        
    def load_documents(self):
        """Load documents from the knowledge base"""
        print("📚 Loading documents from knowledge base...")
        
        if not self.knowledge_base_dir.exists():
            print(f"❌ Knowledge base directory not found: {self.knowledge_base_dir}")
            return []
        
        documents = []
        for md_file in self.knowledge_base_dir.rglob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append({
                        'file': str(md_file),
                        'content': content,
                        'title': md_file.stem
                    })
            except Exception as e:
                print(f"⚠️ Error reading {md_file}: {e}")
        
        self.documents = documents
        print(f"✅ Loaded {len(documents)} documents")
        return documents
    
    def search_documents(self, query: str, max_results: int = 3) -> List[Dict]:
        """Simple keyword-based search"""
        if not self.documents:
            return []
        
        query_lower = query.lower()
        results = []
        
        for doc in self.documents:
            content_lower = doc['content'].lower()
            # Simple keyword matching
            score = 0
            for word in query_lower.split():
                if word in content_lower:
                    score += content_lower.count(word)
            
            if score > 0:
                results.append({
                    'document': doc,
                    'score': score,
                    'title': doc['title']
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:max_results]
    
    def generate_response(self, query: str) -> str:
        """Generate a response based on the knowledge base"""
        # Search for relevant documents
        search_results = self.search_documents(query)
        
        if not search_results:
            return "I don't have specific information about that topic in my knowledge base. Please try asking about NTSA services, driving licenses, vehicle registration, or road safety."
        
        # Build response from search results
        response_parts = []
        
        for i, result in enumerate(search_results[:2], 1):
            doc = result['document']
            content = doc['content']
            
            # Extract relevant sections (first 500 characters)
            relevant_content = content[:500] + "..." if len(content) > 500 else content
            
            response_parts.append(f"Based on NTSA information:\n{relevant_content}")
        
        # Add a helpful note
        response_parts.append("\nFor more specific information, please visit the NTSA website or contact them directly.")
        
        return "\n\n".join(response_parts)
    
    def chat(self, message: str) -> str:
        """Main chat function"""
        if not message.strip():
            return "Please ask me a question about NTSA services!"
        
        # Add to conversation history
        self.conversation_history.append({"user": message, "bot": ""})
        
        # Generate response
        response = self.generate_response(message)
        
        # Update conversation history
        self.conversation_history[-1]["bot"] = response
        
        return response
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
        print("✅ Conversation history cleared")

def main():
    """Main function to run the chatbot"""
    print("🤖 NTSA AI Assistant - Working Version")
    print("=" * 60)
    
    # Initialize chatbot
    chatbot = WorkingChatbot()
    
    # Load documents
    documents = chatbot.load_documents()
    
    if not documents:
        print("❌ No documents found. Please make sure the knowledge base exists.")
        return
    
    print("\n✅ Chatbot ready! Ask me anything about NTSA services!")
    print("Type 'quit' to exit, 'clear' to reset conversation")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                print("👋 Goodbye! Thanks for using NTSA AI Assistant!")
                break
            elif user_input.lower() == 'clear':
                chatbot.reset_conversation()
                continue
            elif not user_input:
                print("Please enter a question.")
                continue
            
            print("🤖 Assistant: ", end="")
            response = chatbot.chat(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
