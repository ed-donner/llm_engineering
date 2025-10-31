import os
import gradio as gr
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

load_dotenv()

# ---- Settings ----
CHROMA_DIR = "chroma"
EMBED_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"

# Initialize components
embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
vectorstore = None
qa_chain = None


def initialize_qa_chain():
    """Initialize the QA chain with the vector store."""
    global vectorstore, qa_chain
    
    if not os.path.exists(CHROMA_DIR):
        return "❌ ChromaDB not found. Please run ingest_gmail_drive.py first to index your emails."
    
    try:
        vectorstore = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings
        )
        
        # Create custom prompt
        prompt_template = """Use the following pieces of context from Gmail emails to answer the question. 
If you don't know the answer based on the context, just say you don't have that information in the emails.

Context:
{context}

Question: {question}

Answer:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )
        
        return "✓ Ready to answer questions about your emails!"
    except Exception as e:
        return f"❌ Error initializing: {str(e)}"


def query_emails(question, num_results=5):
    """Query the email database."""
    if qa_chain is None:
        return "Please click 'Initialize System' first!", ""
    
    if not question.strip():
        return "Please enter a question.", ""
    
    try:
        # Get answer
        result = qa_chain({"query": question})
        answer = result['result']
        
        # Format sources
        sources_text = "\n\n---\n\n**📧 Source Emails:**\n\n"
        for i, doc in enumerate(result['source_documents'][:num_results], 1):
            sources_text += f"**Email {i}:**\n"
            sources_text += f"- **Subject:** {doc.metadata.get('subject', 'N/A')}\n"
            sources_text += f"- **From:** {doc.metadata.get('from', 'N/A')}\n"
            sources_text += f"- **Date:** {doc.metadata.get('date', 'N/A')}\n"
            sources_text += f"- **Preview:** {doc.page_content[:200]}...\n\n"
        
        return answer, sources_text
    except Exception as e:
        return f"❌ Error: {str(e)}", ""


def search_emails(query_text, num_results=5):
    """Direct vector similarity search."""
    if vectorstore is None:
        return "Please click 'Initialize System' first!"
    
    if not query_text.strip():
        return "Please enter a search query."
    
    try:
        docs = vectorstore.similarity_search(query_text, k=num_results)
        
        results_text = f"**Found {len(docs)} relevant emails:**\n\n"
        for i, doc in enumerate(docs, 1):
            results_text += f"**Email {i}:**\n"
            results_text += f"- **Subject:** {doc.metadata.get('subject', 'N/A')}\n"
            results_text += f"- **From:** {doc.metadata.get('from', 'N/A')}\n"
            results_text += f"- **Date:** {doc.metadata.get('date', 'N/A')}\n"
            results_text += f"- **Content Preview:**\n{doc.page_content[:300]}...\n\n"
            results_text += "---\n\n"
        
        return results_text
    except Exception as e:
        return f"❌ Error: {str(e)}"


# Create Gradio Interface
with gr.Blocks(title="Gmail RAG Assistant", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 📧 Gmail RAG Assistant
        Ask questions about your emails or search for specific content.
        """
    )
    
    with gr.Row():
        init_btn = gr.Button("🚀 Initialize System", variant="primary")
        status_text = gr.Textbox(label="Status", interactive=False)
    
    init_btn.click(fn=initialize_qa_chain, outputs=status_text)
    
    gr.Markdown("---")
    
    with gr.Tab("💬 Ask Questions"):
        gr.Markdown("Ask natural language questions about your emails.")
        
        with gr.Row():
            with gr.Column(scale=4):
                question_input = gr.Textbox(
                    label="Your Question",
                    placeholder="What is the latest message from Andela?",
                    lines=2
                )
            with gr.Column(scale=1):
                qa_num_results = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=5,
                    step=1,
                    label="Sources to Show"
                )
        
        qa_btn = gr.Button("Ask Question", variant="primary")
        
        answer_output = gr.Markdown(label="Answer")
        sources_output = gr.Markdown(label="Sources")
        
        qa_btn.click(
            fn=query_emails,
            inputs=[question_input, qa_num_results],
            outputs=[answer_output, sources_output]
        )
        
        # Example questions
        gr.Examples(
            examples=[
                ["What is the latest message from Andela?"],
                ["Summarize emails about project updates"],
                ["What meetings do I have scheduled?"],
                ["Find emails about invoices or payments"],
            ],
            inputs=question_input
        )
    
    with gr.Tab("🔍 Search Emails"):
        gr.Markdown("Search for emails using semantic similarity.")
        
        with gr.Row():
            with gr.Column(scale=4):
                search_input = gr.Textbox(
                    label="Search Query",
                    placeholder="project deadline",
                    lines=2
                )
            with gr.Column(scale=1):
                search_num_results = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=5,
                    step=1,
                    label="Results"
                )
        
        search_btn = gr.Button("Search", variant="primary")
        search_output = gr.Markdown(label="Search Results")
        
        search_btn.click(
            fn=search_emails,
            inputs=[search_input, search_num_results],
            outputs=search_output
        )
        
        gr.Examples(
            examples=[
                ["Andela"],
                ["meeting schedule"],
                ["invoice payment"],
                ["project status update"],
            ],
            inputs=search_input
        )
    
    gr.Markdown(
        """
        ---
        **Note:** Make sure you've run `ingest_gmail_drive.py` first to index your emails.
        """
    )


if __name__ == "__main__":
    demo.launch()