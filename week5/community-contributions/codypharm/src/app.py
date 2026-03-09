import gradio as gr
from src.retrieval.vector_store import PharmaVectorStore
from openai import OpenAI, APIError
from dotenv import load_dotenv
import os
import logging
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)

# Initialize components with error handling
try:
    vector_store = PharmaVectorStore()
    client = OpenAI()
    logger.info("Components initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize components: {str(e)}")
    raise

def _content_str(msg) -> str:
    """Extract string content from a Gradio 6 / OpenAI-style message."""
    if not isinstance(msg, dict):
        return str(msg) if msg else ""
    c = msg.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        # Multimodal: list of parts, e.g. [{"type": "text", "text": "..."}]
        for part in c:
            if isinstance(part, dict) and part.get("type") == "text":
                return part.get("text", "")
            if isinstance(part, str):
                return part
        return ""
    if isinstance(c, dict) and "text" in c:
        return c["text"]
    return str(c) if c else ""


def _normalize_role(msg: dict) -> str | None:
    """Map Gradio role to OpenAI role (Gradio may use 'human' instead of 'user')."""
    role = msg.get("role") if isinstance(msg, dict) else None
    if role == "human":
        return "user"
    if role in ("user", "assistant"):
        return role
    return None


def _build_search_query(message: str, history: List) -> str:
    """
    Build a retrieval query that includes conversation context so follow-ups
    (e.g. "can it be taken by children?") still retrieve the right drug (e.g. Mekinist).
    """
    if not history or not message or len(message) > 200:
        return message.strip()
    # Use last user message for context (the previous question, e.g. about Mekinist)
    for m in reversed(history):
        if not isinstance(m, dict):
            continue
        if _normalize_role(m) == "user":
            prev = _content_str(m).strip()
            if prev and prev != message:
                # Prepend previous question so retrieval finds the same drug/topic
                return f"{prev}\n{message}".strip()
            break
    return message.strip()


def rag_pipeline(message: str, history: List) -> str:
    """
    RAG pipeline with semantic chunking and summary search.

    Gradio 6 passes history as a list of message dicts (role may be "user"/"human"/"assistant").
    """
    
    # Input validation
    if not message or not message.strip():
        return "⚠️ Please ask a question about drug labels."
    
    try:
        # 1. RETRIEVE - Use conversation context so follow-ups retrieve the right drug
        search_query = _build_search_query(message, history or [])
        logger.info(f"Search query: {search_query[:120]}...")
        results = vector_store.search(search_query, k=3)
        
        # Handle empty results
        if not results or not results.get('ids') or not results['ids'][0]:
            return ("❌ I couldn't find relevant information in the drug labels. "
                   "Please try rephrasing your question or ask about a different topic.")
        
        # Extract results
        ids = results['ids'][0]
        metadatas = results['metadatas'][0]
        docs = results['documents'][0]
        
        # Build context and track sources
        context_parts = []
        sources_set = set()
        
        for i, meta in enumerate(metadatas):
            # Get raw content with proper fallback chain
            raw_text = meta.get("raw_content", "")
            
            if not raw_text or raw_text == "No content":
                raw_text = docs[i] if i < len(docs) else ""
    
            if not raw_text:
                continue
            
            section = meta.get("section", "Unknown Section")
            drug = meta.get("drug_name", "Unknown Drug")
            
            # Add to context with clear source markers
            context_parts.append(
                f"--- SOURCE {i+1}: {drug} - {section} ---\n{raw_text}"
            )
            
            # Track unique sources
            sources_set.add(f"{drug} ({section})")
        
        # Validate context
        if not context_parts:
            return ("⚠️ I found some results but couldn't extract meaningful content. "
                   "Please try a different question.")
        
        context_str = "\n\n".join(context_parts)
        logger.info(f"Retrieved {len(context_parts)} relevant sources")
        
        # 2. BUILD MESSAGES
        system_prompt = """You are a Clinical Pharmacist Assistant specializing in drug label interpretation.

INSTRUCTIONS:
- Answer questions STRICTLY based on the provided context from drug labels
- Use the conversation history to resolve follow-up questions (e.g. "it" or "this drug" refers to the drug from the previous question)
- If the answer isn't in the context, say "I cannot find that information in the provided labels"
- Always cite the drug name and section when providing information
- Be precise with dosages, contraindications, and warnings
- If dosing differs by patient population (pediatric, geriatric, renal impairment), specify clearly
- Use clear, professional language appropriate for healthcare settings

IMPORTANT: Do not make assumptions or use external knowledge. Only use the context provided."""

        user_prompt = f"""Context from drug labels:

{context_str}

Question: {message}"""

        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (normalize role: Gradio may send "human" not "user")
        recent = history[-10:] if len(history) > 10 else (history or [])
        for msg in recent:
            if not isinstance(msg, dict):
                continue
            role = _normalize_role(msg)
            content = _content_str(msg)
            if role and content:
                messages.append({"role": role, "content": content})

        # Add current question with context
        messages.append({"role": "user", "content": user_prompt})
        
        # 3. GENERATE - Get LLM response
        logger.info("Generating response with GPT-4o-mini")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0,  # Deterministic for medical info
            max_tokens=800
        )
        
        answer = response.choices[0].message.content
        
        # 4. FORMAT OUTPUT
        sources_list = sorted(list(sources_set))
        sources_str = ", ".join(sources_list) if sources_list else "No sources"
        
        final_output = f"{answer}\n\n---\n📚 **Sources:** {sources_str}"
        logger.info("Response generated successfully")
        return final_output
    
    except APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return ("❌ **API Error:** Unable to generate response. Please check your OpenAI API key "
               "and try again.\n\nError details: " + str(e))
    
    except Exception as e:
        logger.error(f"Error in RAG pipeline: {str(e)}", exc_info=True)
        return (f"❌ **Error:** An unexpected error occurred while processing your question.\n\n"
               f"Please try again or rephrase your query.\n\n"
               f"Technical details: {str(e)}")

# High-contrast CSS: dark background, light text, clear borders
custom_css = """
:root {
    --bg-page: #0f172a;
    --bg-card: #1e293b;
    --bg-input: #334155;
    --border: #475569;
    --text: #f1f5f9;
    --text-muted: #cbd5e1;
    --accent: #38bdf8;
    --accent-strong: #0ea5e9;
}

.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg-page) !important;
    color: var(--text) !important;
}

/* Force readable text everywhere */
.gradio-container *, .wrap, .form, label, span, p {
    color: var(--text) !important;
}

/* Main content */
#component-0 {
    max-width: 1200px;
    margin: auto;
    padding: 2rem;
}

/* Header */
.header-container {
    background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
    padding: 2rem;
    border-radius: 12px;
    color: #ffffff !important;
    margin-bottom: 2rem;
    border: 2px solid #475569;
}

.header-container h1, .header-container p {
    color: #ffffff !important;
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
}

.header-container p {
    margin-top: 0.5rem;
    font-size: 1.1rem;
    font-weight: 400;
}

/* Info panel */
.info-panel {
    background: var(--bg-card) !important;
    border: 2px solid var(--border) !important;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

.info-panel h3 {
    color: var(--accent) !important;
    margin: 0 0 0.75rem 0;
    font-size: 1.1rem;
}

.info-panel li {
    color: var(--text) !important;
    margin: 0.5rem 0;
}

/* Chat area: high contrast */
.chatbot-container {
    background: var(--bg-card) !important;
    border: 2px solid var(--border) !important;
    border-radius: 12px;
    padding: 1rem;
}

.chatbot {
    height: 650px !important;
    border-radius: 8px;
    background: var(--bg-page) !important;
}

/* Chat messages: ensure text is visible */
.chatbot .message, .chatbot .wrap, .chatbot [class*="message"] {
    color: var(--text) !important;
}

.chatbot textarea, .chatbot .prose, .chatbot .markdown {
    color: var(--text) !important;
    background: var(--bg-input) !important;
}

/* Input textbox */
.gradio-container textarea {
    background: var(--bg-input) !important;
    color: var(--text) !important;
    border: 2px solid var(--border) !important;
}

.gradio-container input {
    background: var(--bg-input) !important;
    color: var(--text) !important;
    border: 2px solid var(--border) !important;
}

/* Buttons */
.gradio-container button {
    background: var(--accent-strong) !important;
    color: #ffffff !important;
    border: 2px solid var(--accent) !important;
    font-weight: 600 !important;
}

.gradio-container button:hover {
    background: var(--accent) !important;
    border-color: #7dd3fc !important;
}

/* Example chips/buttons */
.examples button, [class*="example"] button {
    background: var(--bg-input) !important;
    color: var(--text) !important;
    border: 2px solid var(--border) !important;
}

.examples button:hover {
    border-color: var(--accent) !important;
    background: var(--bg-card) !important;
}

/* Footer disclaimer */
.disclaimer {
    background: #422006 !important;
    border: 2px solid #f59e0b !important;
    padding: 1rem 1.5rem;
    border-radius: 6px;
    margin-top: 2rem;
}

.disclaimer strong, .disclaimer {
    color: #fef3c7 !important;
}

/* Catch-all: any content area and markdown in chat */
[class*="chatbot"] .markdown, [class*="chatbot"] .message-content,
.gradio-container [data-testid], .contain, .scroll-hide {
    color: var(--text) !important;
}

/* Block background so Gradio doesn't inject light panels */
.gr-block, .gr-box, .gr-form {
    background: var(--bg-card) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}
"""

# Launch UI (Gradio 6: theme/css go in launch(), not Blocks)
with gr.Blocks() as demo:
    # Header
    gr.HTML("""
        <div class="header-container">
            <h1>Pharma-Aware RAG Agent</h1>
            <p>Ask questions about drug labels using intelligent semantic search powered by RAG</p>
        </div>
    """)
    
    # Info panel
    with gr.Row():
        with gr.Column():
            gr.HTML("""
                <div class="info-panel">
                    <h3>🔍 How It Works</h3>
                    <ul>
                        <li><strong>Semantic Chunking:</strong> Drug labels split by medical sections (DOSAGE, WARNINGS, etc.)</li>
                        <li><strong>Summary Search:</strong> Indexed summaries for precision retrieval</li>
                        <li><strong>RAG Pipeline:</strong> Retrieves relevant sections and generates accurate answers</li>
                        <li><strong>Source Citations:</strong> Every answer includes drug name and section references</li>
                    </ul>
                </div>
            """)
    
    # Chatbot interface
    with gr.Column(elem_classes=["chatbot-container"]):
        chatbot = gr.ChatInterface(
            fn=rag_pipeline,
            chatbot=gr.Chatbot(height=650, show_label=False),
            textbox=gr.Textbox(
                placeholder="Ask about dosage, contraindications, warnings, interactions...",
                show_label=False,
                scale=7
            ),
            submit_btn="Send 🚀",
            examples=[
                "What is the recommended dosage for Mekinist?",
                "What are the contraindications for naproxen?",
                "What were the most common adverse reactions in clinical trials?",
                "Is dose adjustment needed for renal impairment?",
                "What are the drug interactions I should be aware of?",
                "What are the warnings and precautions for varenicline?"
            ],
            cache_examples=False,
        )
    
    # Footer disclaimer
    gr.HTML("""
        <div class="disclaimer">
            <strong>⚠️ Medical Disclaimer:</strong> This tool provides information from drug labels only. 
            Always consult current prescribing information and healthcare professionals for clinical decisions. 
            Not intended for direct patient care.
        </div>
    """)

def launch_app():
    """Launch the Gradio app (shared config for both app.py and main.py)."""
    demo.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7861,
        show_error=True,
        theme=gr.themes.Monochrome(primary_hue="blue"),
        css=custom_css,
        inbrowser=True,
    )


if __name__ == "__main__":
    launch_app()