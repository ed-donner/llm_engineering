import os
import pickle
import argparse
from pathlib import Path
import numpy as np
import openai
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=WORKSPACE_ROOT / ".env")

INDEX_FILE = Path(__file__).parent / "navigator_index.pkl"

class CourseSearcher:
    def __init__(self):
        if not INDEX_FILE.exists():
            raise FileNotFoundError(
                f"Index file not found at {INDEX_FILE}. Please run indexer.py first."
            )
            
        print("Loading search index...")
        with open(INDEX_FILE, "rb") as f:
            index_data = pickle.load(f)
            
        self.chunks = index_data["chunks"]
        self.embeddings = np.array(index_data["embeddings"])
        
        print("Loading local embedding model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Initialize OpenAI client for OpenRouter
        or_key = os.environ.get("OPENROUTER_API_KEY")
        if not or_key:
            # Fallback to check if OPENAI_API_KEY starts with sk-or-v1- (sometimes users set it there)
            open_key = os.environ.get("OPENAI_API_KEY", "")
            if open_key.startswith("sk-or-v1-"):
                or_key = open_key
                
        if or_key:
            self.client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=or_key
            )
        else:
            self.client = None
            print("Warning: OPENROUTER_API_KEY not found in environment. Chat functionality will be disabled, but search will still work.")

    def search(self, query, top_k=5):
        """Perform semantic search using cosine similarity."""
        query_embedding = self.model.encode([query])[0]
        
        # Calculate cosine similarity: A . B / (||A|| * ||B||)
        dot_products = np.dot(self.embeddings, query_embedding)
        norm_embeddings = np.linalg.norm(self.embeddings, axis=1)
        norm_query = np.linalg.norm(query_embedding)
        
        # Avoid division by zero
        similarities = dot_products / (norm_embeddings * norm_query + 1e-8)
        
        # Get top K indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                "chunk": self.chunks[idx],
                "score": float(similarities[idx])
            })
        return results

    def format_results_as_context(self, results):
        """Format retrieved chunks into context block."""
        context_parts = []
        for i, res in enumerate(results, 1):
            meta = res["chunk"]["metadata"]
            file_path = meta.get("file_path", "unknown file")
            
            # Format source location string
            if meta.get("file_type") == "notebook":
                location = f"File: {file_path} (Cell: {meta.get('cell_index')}, Type: {meta.get('cell_type')})"
            elif meta.get("file_type") == "python":
                location = f"File: {file_path} (Lines: {meta.get('line_start')}-{meta.get('line_end')})"
            else:
                location = f"File: {file_path}"
                
            content = res["chunk"]["content"]
            context_parts.append(f"--- Context Source {i} ---\nSource: {location}\nContent:\n{content}\n")
            
        return "\n".join(context_parts)

    def answer_question(self, query, top_k=5, history=None):
        """Retrieve relevant context and generate an answer using OpenRouter."""
        results = self.search(query, top_k=top_k)
        context = self.format_results_as_context(results)
        
        if not self.client:
            return "Error: Cannot generate answer because OpenRouter API Key is missing. Here are the search results:\n\n" + context
            
        system_message = (
            "You are a helpful, expert AI Course Assistant for the 'LLM Engineering' bootcamp repository by Ed Donner.\n"
            "Your job is to answer user questions about the course content, guides, setup, and exercises using the provided context from the codebase.\n"
            "Guidelines:\n"
            "1. Base your answer primarily on the provided Code/Markdown Context. Synthesize it clearly.\n"
            "2. Cite the source files (e.g. week1/day1.ipynb, guides/09_ai_apis_and_ollama.ipynb) when discussing content so the student knows where to look.\n"
            "3. If the context does not contain enough information, state that clearly, but provide a general explanation using your engineering knowledge if helpful.\n"
            "4. Keep formatting clean, using Markdown list items and code formatting where relevant."
        )
        
        messages = [
            {"role": "system", "content": system_message}
        ]
        
        # Append conversation history if present
        if history:
            for turn in history:
                messages.append({"role": "user", "content": turn[0]})
                messages.append({"role": "assistant", "content": turn[1]})
                
        # Append current query with context
        user_content = (
            f"Here is relevant context from the course codebase:\n\n"
            f"{context}\n\n"
            f"User Question: {query}\n\n"
            f"Please answer the user question based on the context above."
        )
        messages.append({"role": "user", "content": user_content})
        
        try:
            # We must specify max_tokens to avoid exceeding low credit balance checks
            # google/gemini-2.5-flash is extremely cost-effective and powerful
            completion = self.client.chat.completions.create(
                model="google/gemini-2.5-flash",
                messages=messages,
                max_tokens=1200,
                temperature=0.3
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error communicating with OpenRouter: {e}\n\nSearch context retrieved:\n\n{context}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Course Navigator CLI Search Tool")
    parser.add_argument("--query", type=str, required=True, help="The search query or question")
    parser.add_argument("--top-k", type=int, default=4, help="Number of search results to retrieve")
    parser.add_argument("--search-only", action="store_true", help="Only show matches without querying OpenRouter")
    
    args = parser.parse_args()
    
    try:
        searcher = CourseSearcher()
        print(f"\nSearching for: '{args.query}'\n")
        results = searcher.search(args.query, top_k=args.top_k)
        
        print("=== SEMANTIC MATCHES ===")
        for i, res in enumerate(results, 1):
            meta = res["chunk"]["metadata"]
            print(f"{i}. [Score: {res['score']:.4f}] {meta.get('file_path')} - type: {meta.get('file_type')}")
            snippet = res["chunk"]["content"].replace("\n", " ")[:120] + "..."
            print(f"   Snippet: {snippet}\n")
            
        if not args.search_only:
            print("=== AI RESPONSE ===")
            answer = searcher.answer_question(args.query, top_k=args.top_k)
            print(answer)
            
    except Exception as e:
        print(f"Error: {e}")
