import os
import sys
from dotenv import load_dotenv

# Configure python path to find 'src' and root project
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_dir = os.path.dirname(parent_dir)
sys.path.append(parent_dir)
sys.path.append(root_dir)

# Load environment variables
dotenv_path = os.path.join(root_dir, ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)

import time
import tempfile
import gradio as gr
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict, Any, Tuple

from src.factory import ProviderFactory
from src.models import ModelManager
from src.audio import transcribe_audio
from src.code_generator import CodeGenerator
from src.compiler import CppCompiler

# Expertise System Prompts
EXPERTISE_PROMPTS = {
    "Software Development": (
        "You are an expert lead software engineer. Your answers should focus on design patterns, "
        "refactoring, algorithms, memory management, and writing clean, maintainable, production-ready code."
    ),
    "DevOps": (
        "You are an expert DevOps and Site Reliability Engineer. Your answers should focus on CI/CD pipelines, "
        "containerization (Docker/Kubernetes), infrastructure as code (Terraform), cloud providers, and system monitoring."
    ),
    "Data Science": (
        "You are an expert data scientist and ML engineer. Your answers should focus on model architectures, "
        "data cleaning, feature engineering, statistical methods, training pipelines (PyTorch/TensorFlow), and hyperparameter tuning."
    ),
    "Security": (
        "You are an expert cybersecurity specialist. Your answers should focus on cryptography, secure coding practices, "
        "OWASP Top 10 vulnerabilities, identity management, network security, and defensive configurations."
    ),
    "Quality Assurance": (
        "You are an expert QA and automation engineer. Your answers should focus on unit testing, integration tests, "
        "end-to-end testing, test automation frameworks (Pytest/Playwright), CI integration, and behavior-driven development."
    ),
    "System Architecture": (
        "You are a principal systems architect. Your answers should focus on distributed systems, microservices vs monoliths, "
        "horizontal scaling, database design (SQL vs NoSQL), caching, message queues, and architectural trade-offs."
    )
}

# Custom Premium Styling CSS
PREMIUM_CSS = """
body {
    font-family: 'Outfit', 'Inter', sans-serif !important;
}
.gradio-container {
    background: linear-gradient(135deg, #101216 0%, #1a1d24 100%) !important;
    color: #e3e6ed !important;
}
.tabs {
    border-bottom: 2px solid #2a2e38 !important;
}
.tab-nav button {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: #8a90a0 !important;
    padding: 10px 20px !important;
    transition: all 0.3s ease !important;
}
.tab-nav button.selected {
    color: #3b82f6 !important;
    border-bottom: 3px solid #3b82f6 !important;
    background-color: rgba(59, 130, 246, 0.05) !important;
}
.tab-nav button:hover {
    color: #60a5fa !important;
}
.control-panel {
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 12px !important;
    padding: 15px !important;
}
.performance-indicator {
    background-color: rgba(16, 185, 129, 0.1) !important;
    border: 1px solid rgba(16, 185, 129, 0.2) !important;
    color: #10b981 !important;
    border-radius: 8px !important;
    padding: 10px !important;
    font-weight: 600 !important;
}
"""

def get_model_choices(provider: str) -> gr.Dropdown:
    models = ModelManager.get_available_models(provider)
    default_val = models[0] if models else ""
    return gr.Dropdown(choices=models, value=default_val)


def handle_qa(
    message: str,
    audio_path: str,
    history: List[Dict[str, str]],
    provider_name: str,
    model_name: str,
    expertise: str
) -> Tuple[List[Dict[str, str]], str, str]:
    """
    Handle Q&A text/audio query, record analytics, and return response.
    """
    # 1. Transcribe audio if provided
    if audio_path:
        transcribed = transcribe_audio(audio_path)
        if transcribed and not transcribed.startswith("["):
            message = transcribed
            print(f"Transcribed voice input: {message}")
        elif transcribed.startswith("["):
            # Append error description to chat
            history.append({"role": "user", "content": "[Voice Input File]"})
            history.append({"role": "assistant", "content": transcribed})
            return history, "", "Error: Transcription failed"

    if not message:
        return history, "", "Warning: No input message provided."

    # 2. Add user message to history
    history.append({"role": "user", "content": message})
    
    # 3. Retrieve system prompt and invoke provider
    system_prompt = EXPERTISE_PROMPTS.get(expertise, "")
    
    # Prepare previous history structure for models.py
    prev_history = history[:-1]
    
    start_time = time.time()
    success = False
    error_msg = ""
    response_content = ""
    
    try:
        provider = ProviderFactory.get_provider(provider_name)
        response_content, latency = provider.generate(
            model_id=model_name,
            prompt=message,
            system_prompt=system_prompt,
            history=prev_history
        )
        success = True
    except Exception as e:
        error_msg = str(e)
        response_content = f"Sorry, an error occurred: {error_msg}"
        latency = time.time() - start_time
    finally:
        ModelManager.log_interaction(
            provider=provider_name,
            model=model_name,
            latency=latency,
            success=success,
            error=error_msg
        )

    # 4. Add assistant response to history
    history.append({"role": "assistant", "content": response_content})
    
    perf_status = f"Provider: {provider_name} | Model: {model_name} | Latency: {latency:.2f}s | Success: {success}"
    return history, "", perf_status


def handle_translate(
    python_code: str,
    provider_name: str,
    model_name: str
) -> Tuple[str, str]:
    """
    Translate Python code to C++.
    """
    if not python_code.strip():
        return "// Please paste or write some Python code.", "Status: Waiting for input"
        
    try:
        generator = CodeGenerator(provider_name, model_name)
        cpp_code, latency = generator.translate(python_code)
        return cpp_code, f"Translation complete in {latency:.2f} seconds."
    except Exception as e:
        return f"// Translation failed: {str(e)}", f"Error: {str(e)}"


def handle_compile_and_run(cpp_code: str) -> Tuple[str, str, str, str]:
    """
    Compile C++ code locally or via Godbolt Compiler Explorer.
    """
    if not cpp_code.strip() or cpp_code.startswith("// Please paste"):
        return "No C++ code to compile.", "", "", "Status: No code provided"

    compiler = CppCompiler()
    result = compiler.compile_and_run(cpp_code)
    
    status = f"Compilation Method: {result['method'].upper()} ({result['compiler']}) | Success: {result['success']}"
    
    compilation_error = result.get("compilation_error", "")
    exec_stdout = result.get("execution_stdout", "")
    exec_stderr = result.get("execution_stderr", "")
    assembly = result.get("assembly", "")

    return compilation_error, exec_stdout, exec_stderr, assembly, status


def generate_analytics_plots() -> Tuple[plt.Figure, pd.DataFrame]:
    """
    Load analytics.json and build Matplotlib visual report charts.
    """
    logs = ModelManager.get_analytics()
    if not logs:
        # Create empty plot
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, "No analytics data recorded yet.\nInteract with Q&A or Code Gen to log metrics.", 
                ha='center', va='center', fontsize=12, color='gray')
        ax.axis('off')
        return fig, pd.DataFrame()

    df = pd.DataFrame(logs)
    
    # Setup plotting style
    plt.style.use('dark_background')
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_alpha(0.0) # Transparent background

    # 1. Bar Chart: Average Latency by Provider
    avg_latency = df.groupby('provider')['latency'].mean().reset_index()
    axes[0].bar(avg_latency['provider'], avg_latency['latency'], color=['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'])
    axes[0].set_title("Average Latency by Provider (seconds)", fontsize=12, fontweight='bold', color='#e3e6ed')
    axes[0].set_ylabel("Seconds", color='#8a90a0')
    axes[0].tick_params(colors='#8a90a0')
    axes[0].grid(axis='y', linestyle='--', alpha=0.3)

    # 2. Stacked Bar Chart: Success vs Failure counts by Model
    success_counts = df.groupby(['model', 'success']).size().unstack(fill_value=0).reset_index()
    if True not in success_counts.columns:
        success_counts[True] = 0
    if False not in success_counts.columns:
        success_counts[False] = 0
        
    models = success_counts['model']
    successes = success_counts[True]
    failures = success_counts[False]

    axes[1].bar(models, successes, label='Success', color='#10b981')
    axes[1].bar(models, failures, bottom=successes, label='Failure', color='#ef4444')
    axes[1].set_title("Request Success/Failure Distribution by Model", fontsize=12, fontweight='bold', color='#e3e6ed')
    axes[1].tick_params(colors='#8a90a0', labelrotation=45)
    axes[1].legend()

    plt.tight_layout()
    return fig, df[['timestamp', 'provider', 'model', 'latency', 'success']]


def handle_reset_analytics():
    ModelManager.reset_analytics()
    fig, df = generate_analytics_plots()
    return fig, df, "Status: Analytics data cleared."


# Construct main Blocks UI
def create_ui():
    with gr.Blocks(title="Questher v3 - AI Developer Platform", css=PREMIUM_CSS) as demo:
        gr.Markdown("""
        # 🚀 Questher v3
        ### Unified Multi-Provider AI Assistant, Code Generator & Compiler Sandbox
        """)

        with gr.Tabs():
            # TAB 1: TECHNICAL Q&A
            with gr.TabItem("Technical Q&A", id="qa_tab"):
                with gr.Row():
                    # Left Settings Sidebar
                    with gr.Column(scale=1, variant="panel"):
                        gr.Markdown("### Provider Configurations")
                        provider_dropdown = gr.Dropdown(
                            choices=list(ModelManager.PROVIDERS_CATALOG.keys()),
                            value="OpenRouter",
                            label="Select AI Provider"
                        )
                        model_dropdown = gr.Dropdown(
                            choices=ModelManager.PROVIDERS_CATALOG["OpenRouter"],
                            value=ModelManager.PROVIDERS_CATALOG["OpenRouter"][0],
                            label="Select Model"
                        )
                        expertise_dropdown = gr.Dropdown(
                            choices=list(EXPERTISE_PROMPTS.keys()),
                            value="Software Development",
                            label="Select Expertise Persona"
                        )
                        
                        gr.Markdown("### Voice Input")
                        audio_input = gr.Audio(
                            label="Record Question (Microphone)",
                            sources=["microphone"],
                            type="filepath"
                        )

                        perf_box = gr.Textbox(
                            label="Performance Metric Monitor",
                            value="Status: Ready",
                            interactive=False,
                            elem_classes=["performance-indicator"]
                        )

                    # Right Chat Area
                    with gr.Column(scale=3):
                        chatbot = gr.Chatbot(
                            label="Conversation Workspace",
                            height=500,
                            type="messages"
                        )
                        with gr.Row():
                            with gr.Column(scale=4):
                                msg_textbox = gr.Textbox(
                                    label="Type your technical question here...",
                                    placeholder="Explain how self-attention works in Transformer models...",
                                    lines=2
                                )
                            with gr.Column(scale=1):
                                submit_btn = gr.Button("Submit Query", variant="primary", scale=1)
                                clear_btn = gr.Button("Clear Chat History", scale=1)

                # Interactions
                provider_dropdown.change(
                    fn=get_model_choices,
                    inputs=provider_dropdown,
                    outputs=model_dropdown
                )

                submit_btn.click(
                    fn=handle_qa,
                    inputs=[msg_textbox, audio_input, chatbot, provider_dropdown, model_dropdown, expertise_dropdown],
                    outputs=[chatbot, msg_textbox, perf_box]
                )
                msg_textbox.submit(
                    fn=handle_qa,
                    inputs=[msg_textbox, audio_input, chatbot, provider_dropdown, model_dropdown, expertise_dropdown],
                    outputs=[chatbot, msg_textbox, perf_box]
                )
                clear_btn.click(
                    fn=lambda: ([], "", "Status: Chat history cleared"),
                    outputs=[chatbot, msg_textbox, perf_box]
                )

            # TAB 2: PYTHON-TO-C++ SANDBOX
            with gr.TabItem("Python-to-C++ Sandbox", id="sandbox_tab"):
                with gr.Row():
                    # Left side: Code conversion
                    with gr.Column(scale=2):
                        gr.Markdown("### 1. Python Input Code")
                        python_editor = gr.Code(
                            language="python",
                            label="Python Workspace",
                            lines=12,
                            value='def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n - 1) + fibonacci(n - 2)\n\nprint("Fibonacci of 10 is:", fibonacci(10))'
                        )
                        with gr.Row():
                            codegen_provider = gr.Dropdown(
                                choices=list(ModelManager.PROVIDERS_CATALOG.keys()),
                                value="OpenRouter",
                                label="AI Provider"
                            )
                            codegen_model = gr.Dropdown(
                                choices=ModelManager.PROVIDERS_CATALOG["OpenRouter"],
                                value=ModelManager.PROVIDERS_CATALOG["OpenRouter"][0],
                                label="Translation Model"
                            )
                        
                        translate_btn = gr.Button("Translate to C++17 ➔", variant="primary")
                        translation_status = gr.Textbox(
                            label="Translation Latency",
                            value="Status: Idle",
                            interactive=False
                        )

                    # Right side: C++ Code Compile & Run
                    with gr.Column(scale=2):
                        gr.Markdown("### 2. C++ Output & Execution Sandbox")
                        cpp_editor = gr.Code(
                            language="cpp",
                            label="Generated C++ Code (Editable)",
                            lines=16,
                            value="// Generated C++ code will appear here..."
                        )
                        
                        compile_btn = gr.Button("🔨 Compile & Execute C++ Program", variant="stop")
                        compile_status = gr.Textbox(
                            label="Compilation Status Monitor",
                            value="Status: Idle",
                            interactive=False
                        )

                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("### 3. Compilation Warnings & Errors")
                        compile_err_box = gr.Textbox(
                            label="Compiler Output Log",
                            placeholder="Errors and warnings from compile step...",
                            lines=6
                        )
                        
                        gr.Markdown("### 4. Executable Output")
                        exec_stdout_box = gr.Textbox(
                            label="Program STDOUT",
                            placeholder="Stdout stream output...",
                            lines=5
                        )
                        exec_stderr_box = gr.Textbox(
                            label="Program STDERR",
                            placeholder="Stderr stream output...",
                            lines=3
                        )

                    with gr.Column(scale=2):
                        gr.Markdown("### 5. Compiled Assembly Output (.s)")
                        assembly_box = gr.Code(
                            language=None,
                            label="Interactive Assembly Viewer",
                            lines=16
                        )

                # Interactions
                codegen_provider.change(
                    fn=get_model_choices,
                    inputs=codegen_provider,
                    outputs=codegen_model
                )

                translate_btn.click(
                    fn=handle_translate,
                    inputs=[python_editor, codegen_provider, codegen_model],
                    outputs=[cpp_editor, translation_status]
                )

                compile_btn.click(
                    fn=handle_compile_and_run,
                    inputs=cpp_editor,
                    outputs=[compile_err_box, exec_stdout_box, exec_stderr_box, assembly_box, compile_status]
                )

            # TAB 3: ANALYTICS & METRICS
            with gr.TabItem("Analytics & System Performance", id="analytics_tab"):
                gr.Markdown("### System Latency & Request Tracking Dashboard")
                with gr.Row():
                    refresh_analytics_btn = gr.Button("🔄 Refresh Live Analytics Charts", variant="primary")
                    reset_analytics_btn = gr.Button("⚠️ Clear Analytics Log History", variant="secondary")
                
                with gr.Row():
                    analytics_plot = gr.Plot(label="Live Performance Analytics Graphs")
                    
                with gr.Row():
                    analytics_table = gr.Dataframe(
                        label="Raw Performance Metrics Log Table",
                        interactive=False
                    )

                # Interactions
                refresh_analytics_btn.click(
                    fn=generate_analytics_plots,
                    outputs=[analytics_plot, analytics_table]
                )
                
                reset_analytics_btn.click(
                    fn=handle_reset_analytics,
                    outputs=[analytics_plot, analytics_table]
                )
                
                # Automatically load plot on tab selection/render
                demo.load(
                    fn=generate_analytics_plots,
                    outputs=[analytics_plot, analytics_table]
                )

    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(server_port=7865)
