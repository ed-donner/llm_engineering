import os
import modal

# --- 1. Infrastructure Setup ---
app = modal.App("legal-multi-agent-ui")

vllm_image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install(
        "vllm==0.10.2", 
        "torch==2.8.0", 
        "huggingface_hub[hf_transfer]==0.35.0"
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

ui_image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install(
        "fastapi[standard]==0.115.4", 
        "gradio~=4.44.1", 
        "pydantic==2.10.1",
        "huggingface-hub==0.36.0" 
    )
)

# MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"
MODEL_NAME = "cjayprime/distilgpt2-finetuned-legalqa"
_llm = None

# --- 2. The Universal LLM Agent Function ---
@app.function(
    image=vllm_image,
    gpu="L4",
    timeout=600,
    # keep_warm=1, # This costs money
    secrets=[modal.Secret.from_name("huggingface-secret")],
)
def run_agent(persona_prompt: str, user_input: str, max_tokens: int = 512) -> str:
    global _llm
    from vllm import LLM, SamplingParams

    tok = os.environ.get("HUGGINGFACE_HUB_TOKEN") or os.environ.get("HF_TOKEN")
    if tok and not os.environ.get("HUGGINGFACE_HUB_TOKEN"):
        os.environ["HUGGINGFACE_HUB_TOKEN"] = tok

    if _llm is None:
        _llm = LLM(
            model=MODEL_NAME, 
            trust_remote_code=True, 
            dtype="auto", 
            tensor_parallel_size=1
        )

    messages = [
        {"role": "system", "content": persona_prompt},
        {"role": "user", "content": user_input}
    ]

    tokenizer = _llm.get_tokenizer()
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    result = _llm.generate([prompt], SamplingParams(max_tokens=max_tokens, temperature=0.3))
    return result[0].outputs[0].text


# --- 3. The Fancy Gradio Web UI ---
@app.function(
    image=ui_image,
    max_containers=1,
)
@modal.asgi_app()
@modal.concurrent(max_inputs=10)
def serve_ui():
    import gradio as gr
    from fastapi import FastAPI
    from gradio.routes import mount_gradio_app
    
    web_app = FastAPI()

    with gr.Blocks(theme=gr.themes.Soft(), title="Agentic Legal RAG") as interface:
        gr.HTML("<h1 style='text-align: center;'>⚖️ Multi-Agent Legal RAG Pipeline</h1>")
        
        # New Status Tracker
        status_display = gr.Markdown("### 🚦 System Status: Ready")
        
        with gr.Row():
            user_query = gr.Textbox(
                label="Enter your legal question:", 
                placeholder="e.g., What are the exceptions to murder under the IPC?", 
                scale=4
            )
            submit_btn = gr.Button("Run Agents 🚀", variant="primary", scale=1)

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 🕵️ Agent 1: Query Expander")
                agent1_out = gr.Textbox(label="JSON Search Vectors", lines=10, interactive=False)
            with gr.Column():
                gr.Markdown("### 📚 Agent 2: Legal Researcher")
                agent2_out = gr.Textbox(label="Simulated Retrieval & Notes", lines=10, interactive=False)
            with gr.Column():
                gr.Markdown("### 🧑‍⚖️ Agent 3: Senior Counsel")
                agent3_out = gr.Textbox(label="Final Opinion", lines=10, interactive=False)

        def process_pipeline(query):
            # Step 1
            yield "### 🚦 System Status: 🕵️ Agent 1 is thinking...", "Working...", "", ""
            p1 = "You are a Search Query Expander. Return 4-5 variants of the user's legal query as a JSON array of strings. Do not include any other text."
            out1 = run_agent.remote(p1, query, 256)
            
            # Step 2
            yield "### 🚦 System Status: 📚 Agent 2 is researching...", out1, "Working...", ""
            p2 = "You are a Legal Researcher. Summarize the relevant Indian penal sections and bare acts for this topic. Be factual."
            out2 = run_agent.remote(p2, f"Queries: {out1}\n\nQuestion: {query}", 512)
            
            # Step 3
            yield "### 🚦 System Status: 🧑‍⚖️ Agent 3 is drafting...", out1, out2, "Working..."
            p3 = "You are a Senior Legal Counsel. Provide a clear, authoritative final answer based on the researcher's notes."
            out3 = run_agent.remote(p3, f"Question: {query}\n\nNotes: {out2}", 1024)
            
            yield "### 🚦 System Status: ✅ Complete", out1, out2, out3

        submit_btn.click(
            fn=process_pipeline,
            inputs=[user_query],
            outputs=[status_display, agent1_out, agent2_out, agent3_out]
        )

    return mount_gradio_app(app=web_app, blocks=interface, path="/")