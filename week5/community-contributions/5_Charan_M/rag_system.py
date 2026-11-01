#.\.venv\Scripts\Activate.ps1
import os
import glob
from dotenv import load_dotenv
from pathlib import Path
import gradio as gr
from openai import OpenAI

# Setting up environment variables
load_dotenv(override=True)
nvidia_api_key = os.getenv('NVIDIA_API_KEY')
if not nvidia_api_key:
    print("Warning: NVIDIA API Key not set")

MODEL = "nvidia/nemotron-3-ultra-550b-a55b"
openai_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=nvidia_api_key
)

class RAGSystem:
    def __init__(self, knowledge_base_path="../../knowledge-base/medical"):
        self.knowledge = {}
        self.knowledge_base_path = knowledge_base_path
        self._load_knowledge()
        
    def _load_knowledge(self):
        """Loads knowledge from text files in the knowledge base path."""
        filenames = glob.glob(f"{self.knowledge_base_path}/*")
        for filename in filenames:
            name = Path(filename).stem.split(' ')[-1]
            with open(filename, "r", encoding="utf-8") as f:
                self.knowledge[name.lower()] = f.read()
        print(f"Loaded {len(self.knowledge)} documents into the knowledge base.")

    def get_relevant_context(self, message):
        """Simple retrieval function that matches words in the query to documents."""
        text = ''.join(ch for ch in message if ch.isalpha() or ch.isspace())
        words = text.lower().split()
        return [self.knowledge[word] for word in words if word in self.knowledge]

    def additional_context(self, message):
        """Formats the retrieved context for the LLM prompt."""
        relevant_context = self.get_relevant_context(message)
        if not relevant_context:
            return "There is no additional context relevant to the user's question."
        
        result = "The following additional context might be relevant in answering the user's question:\n\n"
        result += "\n\n".join(relevant_context)
        return result

    def chat(self, message, history):
        """Main chat function that handles the interaction with the LLM."""
        system_prefix = """
        You represent MediLLM, an advanced Medical AI assistant.
        You are an expert in answering questions about medical conditions, treatments, and patient care.
        You are provided with additional context from medical records or literature that might be relevant to the user's question.
        Give brief, accurate answers. If you don't know the answer, say so. Do not provide unverified medical advice.
        
        Relevant context:
        """
        system_message = system_prefix + self.additional_context(message)
        
        messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
        
        try:
            response = openai_client.chat.completions.create(
                model=MODEL, 
                messages=messages,
                temperature=0.2,
                top_p=0.7,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error connecting to NVIDIA API: {str(e)}"

if __name__ == "__main__":
    print("Initializing RAG System...")
    rag = RAGSystem()
    
    print("Launching Gradio Chat Interface...")
    greeting = "Hello! I am MediLLM, an advanced Medical AI assistant. I can answer questions based on the medical knowledge base. How can I assist you today?"
    chatbot = gr.Chatbot(value=[{"role": "assistant", "content": greeting}])
    view = gr.ChatInterface(rag.chat, chatbot=chatbot).launch(inbrowser=True)
