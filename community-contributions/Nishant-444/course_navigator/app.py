import os
import subprocess
import threading
from pathlib import Path
import gradio as gr
from dotenv import load_dotenv

# Set paths
CURRENT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = CURRENT_DIR.parent.parent.parent
INDEX_FILE = CURRENT_DIR / "navigator_index.pkl"

# Initialize searcher lazily
searcher = None
searcher_error = None

def load_searcher():
    global searcher, searcher_error
    try:
        from searcher import CourseSearcher
        searcher = CourseSearcher()
        searcher_error = None
        return True
    except Exception as e:
        searcher = None
        searcher_error = str(e)
        return False

# Initial attempt to load searcher
load_searcher()

# Lock for indexer threads
indexer_lock = threading.Lock()
indexing_in_progress = False

def run_indexer_thread():
    global indexing_in_progress
    with indexer_lock:
        indexing_in_progress = True
    try:
        # Run indexer script
        indexer_path = CURRENT_DIR / "indexer.py"
        python_exe = WORKSPACE_ROOT / ".venv" / "Scripts" / "python.exe"
        if not python_exe.exists():
            python_exe = "python"
            
        result = subprocess.run(
            [str(python_exe), str(indexer_path)],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_ROOT)
        )
        if result.returncode == 0:
            load_searcher()
            status = "Success: Index built successfully! Reloaded searcher."
        else:
            status = f"Error running indexer: {result.stderr}"
    except Exception as e:
        status = f"Failed to run indexer: {e}"
    finally:
        with indexer_lock:
            indexing_in_progress = False
    return status

def trigger_indexing():
    global indexing_in_progress
    if indexing_in_progress:
        return "Indexing is already running in the background. Please wait..."
        
    thread = threading.Thread(target=run_indexer_thread)
    thread.start()
    return "Indexing started in the background. Please check back in a minute. Reloading searcher upon completion..."

def get_status_md():
    if indexing_in_progress:
        return "⏳ **System Status:** Indexing in progress in the background..."
    if searcher:
        return f"🟢 **System Status:** Connected to index containing **{len(searcher.chunks)}** codebase chunks."
    else:
        return "🔴 **System Status:** No search index found. Please click **Build/Rebuild Index** below."

# Gradio chatbot handling
def chat_respond(message, history):
    global searcher
    if not searcher:
        # Try to reload
        if not load_searcher():
            return history + [{"role": "assistant", "content": f"⚠️ Search index is not loaded. Error: {searcher_error or 'No index found.'}. Please build the index first using the utility tab."}]
            
    # Format history into the tuple format searcher expects
    history_tuples = []
    # History in Gradio 5.x can be list of dicts: [{'role': 'user', 'content': '...'}, {'role': 'assistant', 'content': '...'}]
    temp_user = None
    for item in history:
        if item['role'] == 'user':
            temp_user = item['content']
        elif item['role'] == 'assistant' and temp_user is not None:
            history_tuples.append((temp_user, item['content']))
            temp_user = None

    # Get answer
    answer = searcher.answer_question(message, top_k=4, history=history_tuples)
    
    # Return updated history
    return history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer}
    ]

# Gradio search handling
def explore_search(query, top_k):
    global searcher
    if not searcher:
        if not load_searcher():
            return f"⚠️ Search index is not loaded. Error: {searcher_error or 'No index found.'}."
            
    try:
        results = searcher.search(query, top_k=int(top_k))
        if not results:
            return "No matches found."
            
        md_output = ""
        for i, res in enumerate(results, 1):
            meta = res["chunk"]["metadata"]
            file_path = meta.get("file_path", "unknown")
            file_type = meta.get("file_type", "unknown")
            score = res["score"]
            content = res["chunk"]["content"]
            
            # Create a header
            if file_type == "notebook":
                loc = f"Cell {meta.get('cell_index')} ({meta.get('cell_type')})"
            elif file_type == "python":
                loc = f"Lines {meta.get('line_start')}-{meta.get('line_end')}"
            else:
                loc = "Markdown Section"
                
            md_output += f"### {i}. [{file_type.upper()}] {file_path} - {loc}\n"
            md_output += f"**Relevance Score:** `{score:.4f}`\n\n"
            
            # Wrap content based on type for markdown rendering
            if file_type == "python" or (file_type == "notebook" and meta.get("cell_type") == "code"):
                md_output += f"```python\n{content}\n```\n\n"
            else:
                md_output += f"> {content.replace('\n', '\n> ')}\n\n"
            md_output += "---\n\n"
            
        return md_output
    except Exception as e:
        return f"Error during search: {e}"

# Build custom premium theme
theme = gr.themes.Soft(
    primary_hue="orange",
    secondary_hue="slate",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Outfit"), "sans-serif"]
)

# Custom CSS for glowing dark aesthetic and styling overrides
custom_css = """
.container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 20px;
}
.header-box {
    text-align: center;
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border-radius: 12px;
    padding: 30px;
    margin-bottom: 25px;
    border: 1px solid #334155;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}
.header-box h1 {
    color: #f97316 !important;
    font-size: 2.2rem;
    margin-bottom: 10px;
}
.header-box p {
    color: #94a3b8;
    font-size: 1.1rem;
}
.status-bar {
    background-color: #0f172a;
    padding: 10px 15px;
    border-radius: 8px;
    border: 1px solid #1e293b;
    margin-bottom: 20px;
}
"""

with gr.Blocks(theme=theme, css=custom_css, title="Course Navigator & RAG Assistant") as demo:
    with gr.Column(elem_classes="container"):
        # Header Area
        with gr.Column(elem_classes="header-box"):
            gr.Markdown("# 🚀 LLM Engineering Course Navigator")
            gr.Markdown(
                "Semantic Search and Multi-Agent Chat Assistant. Search guides, code, "
                "and exercise solutions across all 8 weeks of the curriculum."
            )
            
        # Status Bar
        status_md = gr.Markdown(value=get_status_md(), elem_classes="status-bar")
        
        # Tabs
        with gr.Tabs():
            # Chat Assistant Tab
            with gr.Tab("💬 AI Chat Assistant"):
                gr.Markdown(
                    "### Ask questions about the course curriculum and guides\n"
                    "The chatbot will retrieve context from the notebooks/scripts and answer using Gemini on OpenRouter."
                )
                chatbot = gr.Chatbot(type="messages", label="Navigator Chatbot", height=500)
                msg_input = gr.Textbox(
                    placeholder="e.g., How do we set up structured outputs in week 2?",
                    label="Ask a question...",
                    scale=7
                )
                with gr.Row():
                    clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary")
                    submit_btn = gr.Button("📤 Send", variant="primary")
                
                # Chat logic
                def user_submit(message, chat_history):
                    if not message.strip():
                        return "", chat_history
                    new_history = chat_respond(message, chat_history)
                    return "", new_history

                submit_btn.click(user_submit, [msg_input, chatbot], [msg_input, chatbot])
                msg_input.submit(user_submit, [msg_input, chatbot], [msg_input, chatbot])
                clear_btn.click(lambda: [], None, chatbot)

            # Semantic Search Explorer Tab
            with gr.Tab("🔍 Code & Guide Explorer"):
                gr.Markdown("### Search the entire course codebase semantically")
                with gr.Row():
                    search_input = gr.Textbox(
                        placeholder="e.g. prompt engineering strategies, docker setup, or tools config",
                        label="Enter search terms..."
                    )
                    top_k_slider = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=4,
                        step=1,
                        label="Number of matches to retrieve"
                    )
                search_btn = gr.Button("🔍 Search Codebase", variant="primary")
                search_results = gr.Markdown(label="Semantic Matches")
                
                search_btn.click(
                    explore_search,
                    [search_input, top_k_slider],
                    search_results
                )
                search_input.submit(
                    explore_search,
                    [search_input, top_k_slider],
                    search_results
                )

            # Utility Tab
            with gr.Tab("🛠️ Indexer & Setup"):
                gr.Markdown("### Index Management Utility")
                gr.Markdown(
                    "If you make changes to notebooks, python scripts, or add personal notes in any of "
                    "the folders, you can rebuild the vector database index. Rebuilding uses "
                    "`sentence-transformers` locally and takes about 1-2 minutes."
                )
                build_btn = gr.Button("🔄 Rebuild Search Index", variant="primary")
                build_output = gr.Textbox(label="Status Logs / Outputs", interactive=False)
                
                def on_build_click():
                    msg = trigger_indexing()
                    return msg
                
                # We can also update status_md with a refresh function
                def refresh_status():
                    return get_status_md()
                
                build_btn.click(on_build_click, None, build_output)
                # Auto refresh status when switching or after action
                demo.load(refresh_status, None, status_md)
                
    gr.Markdown(
        "<center>Course Navigator & RAG Assistant | Created as a community contribution by Nishant Sharma</center>"
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
