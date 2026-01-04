"""
Python to C++ Code Optimizer - AI-Powered Code Conversion
Modern Gradio app with password protection for secure deployments

Supported Models:
- GPT-4o (OpenAI) - Premium, fastest, most accurate
- Claude-3.5-Sonnet (Anthropic) - Premium, excellent for code

⚠️ SECURITY WARNING:
This app executes arbitrary code. Only run code from trusted sources.
Malicious code can harm the system. Use at your own risk.
"""

import os
import io
import sys
import subprocess
import socket
import httpx
from openai import OpenAI
import anthropic
# Workaround for Python 3.13 where stdlib audioop is removed; instruct pydub to use pure-python fallback
os.environ.setdefault("PYDUB_SIMPLE_AUDIOOP", "1")
import gradio as gr

# Try to load from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# PASSWORD PROTECTION
# Set this as a Hugging Face Secret: APP_PASSWORD
APP_PASSWORD = os.environ.get("APP_PASSWORD", "demo123")  # Change default!

# Lazy initialization of AI clients with explicit HTTP client to avoid Gradio conflicts
def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found. Please set it in your environment or .env file.")
    
    # Create a clean HTTP client without proxies to avoid Gradio conflicts
    http_client = httpx.Client(
        timeout=60.0,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )
    
    return OpenAI(api_key=api_key, http_client=http_client)

def get_claude_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found. Please set it in your environment or .env file.")
    
    # Create a clean HTTP client without proxies to avoid Gradio conflicts
    http_client = httpx.Client(
        timeout=60.0,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )
    
    return anthropic.Anthropic(api_key=api_key, http_client=http_client)

# Model configurations
OPENAI_MODEL = "gpt-4o"
CLAUDE_MODEL = "claude-3-5-sonnet-20240620"

# System and user prompts
system_message = (
    "You are an assistant that reimplements Python code in high performance C++. "
    "Respond only with C++ code; use comments sparingly and do not provide any explanation other than occasional comments. "
    "The C++ response needs to produce an identical output in the fastest possible time."
)

def user_prompt_for(python):
    user_prompt = (
        "Rewrite this Python code in C++ with the fastest possible implementation that produces identical output in the least time. "
        "Respond only with C++ code; do not explain your work other than a few comments. "
        "Pay attention to number types to ensure no int overflows. Remember to #include all necessary C++ packages such as iomanip.\n\n"
    )
    user_prompt += python
    return user_prompt

def messages_for(python):
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt_for(python)}
    ]

def write_output(cpp):
    """Write C++ code to file for compilation"""
    code = cpp.replace("```cpp","").replace("```","")
    with open("optimized.cpp", "w") as f:
        f.write(code)

def stream_gpt(python):
    """Stream GPT-4o response"""
    try:
        client = get_openai_client()
        stream = client.chat.completions.create(
            model=OPENAI_MODEL, 
            messages=messages_for(python), 
            stream=True
        )
        reply = ""
        for chunk in stream:
            fragment = chunk.choices[0].delta.content or ""
            reply += fragment
            yield reply.replace('```cpp\n','').replace('```','')
    except ValueError as e:
        yield f"❌ Error: {str(e)}"
    except Exception as e:
        yield f"❌ Error: {str(e)}"

def stream_claude(python):
    """Stream Claude response"""
    try:
        client = get_claude_client()
        result = client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            system=system_message,
            messages=[{"role": "user", "content": user_prompt_for(python)}],
        )
        reply = ""
        with result as stream:
            for text in stream.text_stream:
                reply += text
                yield reply.replace('```cpp\n','').replace('```','')
    except ValueError as e:
        yield f"❌ Error: {str(e)}"
    except Exception as e:
        yield f"❌ Error: {str(e)}"

def optimize(python, model):
    """Convert Python to C++ using selected AI model"""
    if model in ["GPT-4o", "GPT"]:
        result = stream_gpt(python)
    elif model in ["Claude-3.5-Sonnet", "Claude"]:
        result = stream_claude(python)
    else:
        raise ValueError(f"Unknown model: {model}")
    
    for stream_so_far in result:
        yield stream_so_far

def execute_python(code):
    """⚠️ WARNING: Executes arbitrary Python code"""
    try:
        output = io.StringIO()
        sys.stdout = output
        exec(code)
    finally:
        sys.stdout = sys.__stdout__
    return output.getvalue()

def execute_cpp(code):
    """⚠️ WARNING: Compiles and executes arbitrary C++ code"""
    write_output(code)
    try:
        compile_cmd = ["g++", "-O3", "-std=c++17", "-o", "optimized", "optimized.cpp"]
        compile_result = subprocess.run(
            compile_cmd, 
            check=True, 
            text=True, 
            capture_output=True,
            timeout=30
        )
        
        run_cmd = ["./optimized"]
        run_result = subprocess.run(
            run_cmd, 
            check=True, 
            text=True, 
            capture_output=True,
            timeout=30
        )
        return run_result.stdout
    except subprocess.TimeoutExpired:
        return "⚠️ Execution timed out (30 seconds limit)"
    except subprocess.CalledProcessError as e:
        return f"❌ An error occurred:\n{e.stderr}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

# Example Python code
default_python = """import time

def calculate(iterations, param1, param2):
    result = 1.0
    for i in range(1, iterations+1):
        j = i * param1 - param2
        result -= (1/j)
        j = i * param1 + param2
        result += (1/j)
    return result

start_time = time.time()
result = calculate(100_000_000, 4, 1) * 4
end_time = time.time()

print(f"Result: {result:.12f}")
print(f"Execution Time: {(end_time - start_time):.6f} seconds")
"""

# Modern CSS
modern_css = """
.gradio-container, body, html {
    background: #f9fafb !important; /* light background to avoid dark-mode conflicts */
    color: #111827 !important;      /* ensure readable text */
}

.gradio-container {
    max-width: 1400px !important;
    margin: 0 auto !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.modern-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 24px;
    border-radius: 16px;
    margin-bottom: 24px;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.modern-header h1 {
    margin: 0;
    font-size: 32px;
    font-weight: 700;
    letter-spacing: -0.5px;
}

.modern-header p {
    margin: 12px 0 0 0;
    opacity: 0.9;
    font-size: 18px;
    font-weight: 400;
}

.security-warning {
    background: #fee2e2 !important;
    border: 2px solid #dc2626 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    margin: 16px 0 !important;
}

.python-input {
    background: #f8fafc !important;
    border: 2px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
    font-size: 14px !important;
    color: #1e293b !important;
    line-height: 1.5 !important;
}

.python-input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

.cpp-output {
    background: #f1f5f9 !important;
    border: 2px solid #cbd5e1 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
    font-size: 14px !important;
    color: #0f172a !important;
    line-height: 1.5 !important;
}

.model-selector {
    background: white !important;
    border: 2px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    font-size: 16px !important;
    color: #374151 !important;
}

.model-selector:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

.modern-button {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px 28px !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 6px rgba(59, 130, 246, 0.2) !important;
}

.modern-button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 12px rgba(59, 130, 246, 0.3) !important;
}

.run-button {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2) !important;
}

.run-button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 8px rgba(16, 185, 129, 0.3) !important;
}

.output-section {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
    margin: 12px 0;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 13px;
    line-height: 1.4;
    color: #374151;
    min-height: 100px;
    overflow-y: auto;
}

.python-output {
    background: #fef3c7 !important;
    border: 2px solid #f59e0b !important;
    color: #92400e !important;
}

.cpp-output-result {
    background: #dbeafe !important;
    border: 2px solid #3b82f6 !important;
    color: #1e40af !important;
}

.performance-card {
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border: 1px solid #0ea5e9;
    border-radius: 12px;
    padding: 20px;
    margin: 16px 0;
    text-align: center;
}

.performance-card h3 {
    margin: 0 0 12px 0;
    color: #0c4a6e;
    font-size: 18px;
    font-weight: 600;
}

.performance-metric {
    display: inline-block;
    background: white;
    border-radius: 8px;
    padding: 8px 16px;
    margin: 4px;
    font-weight: 600;
    color: #0c4a6e;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Login styling */
body, .gradio-container {
    background: url('assets/3656064.jpg') center/cover no-repeat fixed !important;
}

.login-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 24px;
    background: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url('assets/3656064.jpg') center/cover no-repeat fixed;
}

.login-card {
    max-width: 400px;
    width: 100%;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 20px;
    padding: 48px 40px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-icon {
    font-size: 56px;
    text-align: center;
    margin-bottom: 16px;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
}

.login-title {
    text-align: center;
    margin: 0 0 8px 0;
    font-size: 28px;
    font-weight: 700;
    color: #1f2937;
    letter-spacing: -0.02em;
}

.login-subtitle {
    text-align: center;
    margin: 0 0 32px 0;
    font-size: 15px;
    color: #6b7280;
    font-weight: 400;
}

.login-input label {
    color: #374151 !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}

.login-input input {
    background: white !important;
    border: 2px solid #e5e7eb !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    font-size: 16px !important;
    color: #111827 !important;
}

.login-input input:focus {
    border-color: #667eea !important;
    background: white !important;
    outline: none !important;
    box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1) !important;
}

.login-error {
    color: #dc2626;
    background: #fee2e2;
    border: 1px solid #fca5a5;
    padding: 12px;
    border-radius: 10px;
    text-align: center;
    font-weight: 500;
}

.freepik-credit {
    margin-top: 24px;
    text-align: center;
    font-size: 12px;
    color: #9ca3af;
}

.freepik-credit a {
    color: #667eea;
    text-decoration: none;
    font-weight: 500;
}

.freepik-credit a:hover {
    text-decoration: underline;
}
"""

# Create the interface with password protection
def create_interface():
    with gr.Blocks(css=modern_css, title="Python to C++ Code Optimizer", theme=gr.themes.Soft()) as app:
        authorized = gr.State(False)
        # Background image is handled via CSS: assets/3656064.jpg
        # For Hugging Face Space: use /file=assets/3656064.jpg in CSS
        # For local: use assets/3656064.jpg in CSS

        def check_password(pw):
            ok = pw == APP_PASSWORD
            return (
                gr.update(visible=not ok),  # login hidden when ok
                gr.update(visible=ok),      # main shown when ok
                gr.update(value="" if ok else "Invalid password", visible=not ok)
            )

        # Login gate
        with gr.Group(visible=True) as login_group:
            gr.HTML("""
            <div class="login-wrapper">
                <div class="login-card">
                    <div class="login-icon">🔐</div>
                    <div class="login-title">Private Access</div>
                    <div class="login-subtitle">Enter password to continue</div>
            """)
            pw = gr.Textbox(
                label="Password", 
                type="password", 
                placeholder="Enter password", 
                elem_classes=["login-input"],
                container=True
            )
            login_btn = gr.Button("Continue", elem_classes=["modern-button"], size="lg")
            login_error = gr.Markdown(visible=False, elem_classes=["login-error"])
            gr.HTML("""
                    <div class="freepik-credit">Background image by <a href="https://www.freepik.com" target="_blank">Freepik</a></div>
                </div>
            </div>
            """)

        # Main UI wrapped for toggling visibility
        with gr.Group(visible=False) as main_group:
            main_group.elem_id = "main_group"
            # Header Section
            gr.HTML("""
            <div class="modern-header">
                <h1>🚀 Python to C++ Code Optimizer</h1>
                <p>AI-powered code conversion with real-time execution and performance analysis</p>
            </div>
            """)

            # Security Warning
            gr.HTML("""
            <div class="security-warning">
                <h3 style="color: #dc2626; margin: 0 0 8px 0;">⚠️ Security Warning</h3>
                <p style="margin: 0; color: #991b1b; font-weight: 500;">
                    This interface executes arbitrary code. <strong>Only run code from trusted sources.</strong><br>
                    Malicious code can harm your system. Use at your own risk.
                </p>
            </div>
            """)

            # Main Content Area
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📝 Python Code Input")
                    python_input = gr.Textbox(
                        label="Python Code:", 
                        value=default_python, 
                        lines=15,
                        elem_classes=["python-input"],
                        placeholder="Enter your Python code here..."
                    )

                    with gr.Row():
                        model_selector = gr.Dropdown(
                            ["GPT-4o", "Claude-3.5-Sonnet"], 
                            label="Select AI Model", 
                            value="GPT-4o",
                            elem_classes=["model-selector"]
                        )

                    convert_button = gr.Button("✨ Convert to C++", elem_classes=["modern-button"])

                with gr.Column(scale=1):
                    gr.Markdown("### ⚡ Optimized C++ Code")
                    cpp_output = gr.Textbox(
                        label="Generated C++ Code:", 
                        lines=15,
                        elem_classes=["cpp-output"],
                        interactive=False
                    )

            # Execution Section
            gr.Markdown("---")
            gr.Markdown("## 🏃 Code Execution & Performance Comparison")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 🐍 Python Output")
                    run_python_button = gr.Button("▶️ Run Python", elem_classes=["run-button"])
                    python_output = gr.Textbox(
                        label="Python Execution Output:",
                        lines=5,
                        elem_classes=["python-output"],
                        interactive=False
                    )

                with gr.Column():
                    gr.Markdown("### ⚡ C++ Output")
                    run_cpp_button = gr.Button("▶️ Run C++", elem_classes=["run-button"])
                    cpp_execution_output = gr.Textbox(
                        label="C++ Execution Output:",
                        lines=5,
                        elem_classes=["cpp-output-result"],
                        interactive=False
                    )

            # Event handlers
            convert_button.click(
                fn=optimize,
                inputs=[python_input, model_selector],
                outputs=cpp_output
            )

            run_python_button.click(
                fn=execute_python,
                inputs=python_input,
                outputs=python_output
            )

            run_cpp_button.click(
                fn=execute_cpp,
                inputs=cpp_output,
                outputs=cpp_execution_output
            )

        # Bind login after main_group is defined
        login_btn.click(
            fn=check_password,
            inputs=[pw],
            outputs=[login_group, main_group, login_error]
        )

    return app

# Launch the app
if __name__ == "__main__":
    print("\n" + "="*50)
    print(f"===== Application Startup at {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")
    print("="*50)
    
    # Create the app
    app = create_interface()
    
    # Check if running on Hugging Face Spaces
    is_huggingface = os.getenv("SPACE_ID") is not None
    
    if is_huggingface:
        # Hugging Face Spaces configuration
        print("🚀 Launching Python to C++ Code Optimizer on Hugging Face Spaces")
        print("🔐 Password protection enabled")
        app.launch(
            show_error=True
        )
    else:
        # Local development configuration
        def get_available_port(start_port=7860):
            """Find an available port starting from start_port"""
            port = start_port
            while port < start_port + 100:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('', port))
                        return port
                except OSError:
                    port += 1
            return start_port
        
        port = get_available_port()
        print(f"🚀 Launching Python to C++ Code Optimizer on port: {port}")
        print(f"🔐 Password protection enabled. Password: {APP_PASSWORD}")
        
        app.launch(
            server_name="127.0.0.1",
            server_port=port,
            show_error=True
        )

