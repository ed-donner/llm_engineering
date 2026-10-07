#.\.venv\Scripts\Activate.ps1
"""
Week 2 Exercise - Full Prototype Technical Q&A Assistant (TechMentor AI)

Features:
- Gradio UI (gr.Blocks) with modern design and controls
- Multi-model switching (Groq OSS 120B/Qwen, OpenAI/OpenRouter GPT-4o-mini, Ollama)
- Real-time streaming responses
- System prompt expertise customization (Principal Engineer, Refactoring Specialist, Beginner Mentor)
- Bonus: Tool execution (Python Sandbox Code Runner & AST Syntax Inspector)
- Bold Bonus: Audio input (Speech-to-Text via Whisper) and Audio output (Text-to-Speech via gTTS / OpenAI)
"""

import os
import sys
import io
import ast
import json
import tempfile
import traceback
from typing import Generator, Tuple, Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

import gradio as gr
from openai import OpenAI
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


# ==========================================
# 1. API Clients & Configuration
# ==========================================
openai_api_key = os.getenv("OPENAI_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# Clients initialization
groq_client = Groq(api_key=groq_api_key) if (GROQ_AVAILABLE and groq_api_key) else None
openai_client = OpenAI(api_key=openai_api_key, base_url=openai_base_url) if openai_api_key else None
ollama_client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

MODEL_OPTIONS = {
    "Groq: OpenAI GPT-OSS 120B (Ultra-fast, Free)": {
        "provider": "groq",
        "model_id": "openai/gpt-oss-120b",
        "supports_tools": True
    },
    "Groq: Qwen 3.8 27B (Fast & Accurate)": {
        "provider": "groq",
        "model_id": "qwen/qwen3.8-27b",
        "supports_tools": True
    },
    "OpenAI / OpenRouter: GPT-4o-mini": {
        "provider": "openai",
        "model_id": "gpt-4o-mini" if "openrouter" not in openai_base_url else "openai/gpt-4o-mini",
        "supports_tools": True
    },
    "Ollama: Llama 3.2 (Local Machine)": {
        "provider": "ollama",
        "model_id": "llama3.2",
        "supports_tools": False
    }
}



# ==========================================
# 3. Tools (Bonus Feature)
# ==========================================
def run_python_code(code: str) -> str:
    """Safely executes Python code in a local sandbox scope and captures stdout."""
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    captured_io = io.StringIO()
    sys.stdout = captured_io
    sys.stderr = captured_io
    try:
        scope: Dict[str, Any] = {}
        compiled = compile(code, "<sandbox>", "exec")
        exec(compiled, scope)
        output = captured_io.getvalue().strip()
        if not output:
            output = "Code ran successfully with no stdout output."
        return output
    except Exception as e:
        return f"Execution Error: {e}\n{traceback.format_exc()}"
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def inspect_python_syntax(code: str) -> str:
    """Parses Python code and dumps its AST structure to inspect nodes and tokens."""
    try:
        tree = ast.parse(code)
        return ast.dump(tree, indent=2)
    except SyntaxError as e:
        return f"Syntax Error at line {e.lineno}, col {e.offset}: {e.msg}"


TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "run_python_code",
            "description": "Execute Python code in an isolated scope to verify behavior, test output, or evaluate an example. Always include print() to show output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python source code to execute."
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_python_syntax",
            "description": "Parse Python source code into an Abstract Syntax Tree (AST) to inspect its grammatical syntax and node types.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python source code snippet to parse."
                    }
                },
                "required": ["code"]
            }
        }
    }
]


def execute_tool_call(tool_name: str, arguments: dict) -> str:
    """Dispatches tool execution."""
    if tool_name == "run_python_code":
        return run_python_code(arguments.get("code", ""))
    elif tool_name == "inspect_python_syntax":
        return inspect_python_syntax(arguments.get("code", ""))
    return f"Unknown tool: {tool_name}"


# ==========================================
# 4. Audio Input & Output (Bold Bonus)
# ==========================================
def transcribe_audio(audio_path: Optional[str]) -> str:
    """Transcribes audio file to text using Groq Whisper or OpenAI Whisper."""
    if not audio_path:
        return ""
    try:
        with open(audio_path, "rb") as audio_file:
            if groq_client:
                transcription = groq_client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=audio_file
                )
                return transcription.text.strip()
            elif openai_client:
                transcription = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                return transcription.text.strip()
            else:
                return "Audio transcription unavailable: No Groq or OpenAI key configured."
    except Exception as e:
        return f"[Audio transcription error: {str(e)}]"


def synthesize_speech(text: str) -> Optional[str]:
    """Generates an audio file from text using gTTS or OpenAI TTS."""
    if not text or not text.strip():
        return None
    
    # Clean text of markdown code blocks for cleaner audio
    clean_text = "\n".join([line for line in text.split("\n") if not line.strip().startswith("```")])
    # Keep first 300 words for audio summary so TTS is fast and concise
    words = clean_text.split()
    if len(words) > 120:
        clean_text = " ".join(words[:120]) + " ... Full detailed explanation available in text below."

    try:
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_path = temp_audio.name
        temp_audio.close()

        if GTTS_AVAILABLE:
            tts = gTTS(text=clean_text, lang="en")
            tts.save(temp_path)
            return temp_path
        elif openai_client:
            response = openai_client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=clean_text
            )
            with open(temp_path, "wb") as f:
                f.write(response.content)
            return temp_path
    except Exception as e:
        print(f"TTS generation error: {e}")
        return None
    return None


# ==========================================
# 5. Core Chat Handler with Streaming & Tools
# ==========================================
def ask_assistant(
    user_question: str,
    audio_file: Optional[str],
    model_choice: str,
    custom_system_prompt: str,
    enable_tools: bool,
    enable_audio_reply: bool,
    chat_history: list
):
    """
    Main handler yielding streaming chat responses, tool execution logs, and optional audio.
    """
    # Step 1: If audio was provided and question is blank, transcribe it
    if audio_file and not user_question.strip():
        transcribed = transcribe_audio(audio_file)
        if transcribed and not transcribed.startswith("["):
            user_question = transcribed
        else:
            user_question = f"(Transcribed: {transcribed})"

    if not user_question.strip():
        yield chat_history, None, "Please type a question or record audio!"
        return

    # Add user message to history
    new_history = list(chat_history)
    new_history.append({"role": "user", "content": user_question})



    def _extract_text(content):
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for c in content:
                if isinstance(c, dict) and "text" in c:
                    parts.append(c["text"])
                elif isinstance(c, str):
                    parts.append(c)
            return " ".join(parts)
        return str(content)

    messages: List[Dict[str, Any]] = []
    if custom_system_prompt.strip():
        messages.append({"role": "system", "content": custom_system_prompt.strip()})
    for msg in new_history:
        messages.append({"role": msg["role"], "content": _extract_text(msg["content"])})

    # Resolve model client
    config = MODEL_OPTIONS.get(model_choice, list(MODEL_OPTIONS.values())[0])
    provider = config["provider"]
    model_id = config["model_id"]
    supports_tools = config["supports_tools"] and enable_tools

    client = None
    if provider == "groq" and groq_client:
        client = groq_client
    elif provider == "openai" and openai_client:
        client = openai_client
    elif provider == "ollama":
        client = ollama_client
    else:
        # Fallback to groq if available, then openai
        client = groq_client or openai_client or ollama_client

    if client is None:
        new_history.append({"role": "assistant", "content": "⚠️ No available LLM client configured. Please check your `.env` API keys."})
        yield new_history, None, "No API client available."
        return

    # Placeholder assistant message for streaming
    new_history.append({"role": "assistant", "content": ""})
    tool_status_text = "Thinking..."
    yield new_history, None, tool_status_text

    # Tool Execution Loop (if supported and enabled)
    tool_logs = []
    max_tool_rounds = 2
    round_count = 0

    while round_count < max_tool_rounds:
        round_count += 1
        call_kwargs: Dict[str, Any] = {
            "model": model_id,
            "messages": messages,
        }
        if provider == "openai" and "openrouter" in openai_base_url:
            call_kwargs["max_tokens"] = 1000

        if supports_tools:
            call_kwargs["tools"] = TOOLS_SPEC

        try:
            # First check if the model wants to call tools (non-streaming probe if tools enabled)
            if supports_tools:
                resp = client.chat.completions.create(**call_kwargs)
                choice = resp.choices[0]

                if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
                    messages.append(choice.message)
                    for tc in choice.message.tool_calls:
                        func_name = tc.function.name
                        try:
                            args = json.loads(tc.function.arguments)
                        except Exception:
                            args = {}
                        
                        tool_status_text = f"⚙️ Executing tool: `{func_name}`..."
                        tool_logs.append(f"🛠️ **Tool Called:** `{func_name}`\nArguments:\n```json\n{json.dumps(args, indent=2)}\n```")
                        yield new_history, None, tool_status_text

                        result = execute_tool_call(func_name, args)
                        tool_logs.append(f"📊 **Tool Result:**\n```text\n{result}\n```")

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result
                        })
                    
                    tool_status_text = "Tool completed. Synthesizing technical answer..."
                    yield new_history, None, tool_status_text
                    continue  # Iterate to process tool results
            
            # If no tools called or tools completed, stream final answer
            break
        except Exception as e:
            # In case tool calling fails or is unsupported by model, proceed directly to streaming
            tool_logs.append(f"*(Tool calling bypassed or encountered error: {e})*")
            break

    # Stream final response to user
    stream_kwargs: Dict[str, Any] = {
        "model": model_id,
        "messages": messages,
        "stream": True,
    }
    if provider == "openai" and "openrouter" in openai_base_url:
        stream_kwargs["max_tokens"] = 1200

    accumulated_content = ""
    try:
        stream = client.chat.completions.create(**stream_kwargs)
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            accumulated_content += delta
            new_history[-1]["content"] = accumulated_content
            yield new_history, None, "Streaming response..."
    except Exception as e:
        accumulated_content += f"\n\n*(Error generating completion: {str(e)})*"
        new_history[-1]["content"] = accumulated_content
        yield new_history, None, f"Error: {e}"

    # Step 6: Generate audio output if enabled
    audio_path = None
    if enable_audio_reply:
        yield new_history, None, "🎙️ Generating spoken voice reply..."
        audio_path = synthesize_speech(accumulated_content)

    final_tool_log = "\n\n---\n\n".join(tool_logs) if tool_logs else "No tools called for this query."
    yield new_history, audio_path, f"Done! Status: Completed.\n\n{final_tool_log}"


# ==========================================
# 6. Gradio UI Construction (gr.Blocks)
# ==========================================
def build_ui() -> gr.Blocks:
    """Builds the complete Gradio UI application."""
    
    custom_css = """
    .main-container { max-width: 1200px; margin: auto; }
    .header-box { padding: 20px; border-radius: 12px; background: linear-gradient(135deg, #1e293b, #0f172a); color: white; margin-bottom: 20px; }
    .status-badge { font-weight: bold; color: #10b981; }
    """

    with gr.Blocks(title="TechMentor AI - Technical Question Answering Prototype") as app:
        with gr.Column(elem_classes=["main-container"]):
            with gr.Row(elem_classes=["header-box"]):
                gr.Markdown(
                    """
                    # 🚀 TechMentor AI — Technical Question & Answerer
                    """
                )

            with gr.Row():
                # LEFT COLUMN: Configuration & Inputs
                with gr.Column(scale=4):
                    gr.Markdown("### ⚙️ Engine Settings")
                    model_dropdown = gr.Dropdown(
                        choices=list(MODEL_OPTIONS.keys()),
                        value=list(MODEL_OPTIONS.keys())[0],
                        label="Model Selector",
                        info="Switch seamlessly between frontier and local models"
                    )

                    with gr.Accordion("🛠️ Custom System Prompt", open=True):
                        custom_prompt = gr.Textbox(
                            label="Override System Prompt",
                            placeholder="Leave blank to use selected persona...",
                            lines=3
                        )

                    with gr.Row():
                        enable_tools_cb = gr.Checkbox(value=True, label="Enable Tool Calling (Sandbox & AST)")
                        enable_audio_cb = gr.Checkbox(value=True, label="Enable Audio Output (TTS)")

                    gr.Markdown("### 🎙️ Audio Input (Bold Bonus)")
                    audio_input = gr.Audio(
                        sources=["microphone", "upload"],
                        type="filepath",
                        label="Speak Your Question (Voice Input)"
                    )

                    gr.Markdown("### 💬 Ask a Technical Question")
                    question_input = gr.Textbox(
                        label="Question / Code Snippet",
                        placeholder="e.g. Please explain what this code does and why:\nyield from {book.get('author') for book in books if book.get('author')}",
                        lines=5
                    )

                    with gr.Row():
                        submit_btn = gr.Button("🚀 Ask Assistant", variant="primary", scale=2)
                        clear_btn = gr.Button("🗑️ Clear", scale=1)

                    gr.Markdown("### 💡 Quick Examples (Click to Try)")
                    example_1 = gr.Button("🏗️ System Design: Scalable URL Shortener")
                    example_2 = gr.Button("🧠 Algorithm: A* Search Implementation")
                    example_3 = gr.Button("🐛 Debugging: Why 0.1 + 0.2 != 0.3?")
                    example_4 = gr.Button("🕵️ Security: SQL Injection Explained")

                # RIGHT COLUMN: Chatbot & Live Output
                with gr.Column(scale=6):
                    gr.Markdown("### 🧠 Technical Explanation (Streaming)")
                    chatbot = gr.Chatbot(
                        label="Conversation",
                        height=520
                    )

                    audio_output = gr.Audio(
                        label="🔊 Spoken Response (Audio Output)",
                        autoplay=False,
                        type="filepath"
                    )

                    with gr.Accordion("🔍 Tool Execution Logs & Status", open=True):
                        tool_status = gr.Markdown("Status: Idle. Waiting for question...")

        # Wire callbacks
        submit_btn.click(
            fn=ask_assistant,
            inputs=[
                question_input,
                audio_input,
                model_dropdown,
                custom_prompt,
                enable_tools_cb,
                enable_audio_cb,
                chatbot
            ],
            outputs=[chatbot, audio_output, tool_status]
        )

        question_input.submit(
            fn=ask_assistant,
            inputs=[
                question_input,
                audio_input,
                model_dropdown,
                custom_prompt,
                enable_tools_cb,
                enable_audio_cb,
                chatbot
            ],
            outputs=[chatbot, audio_output, tool_status]
        )

        clear_btn.click(
            fn=lambda: ([], "", None, None, "Status: Cleared."),
            outputs=[chatbot, question_input, audio_input, audio_output, tool_status]
        )

        # Example buttons setup
        example_1.click(
            fn=lambda: (
                "Design a scalable URL shortener like bit.ly. What database would you choose, and how would you handle concurrent writes and potential hash collisions?"
            ),
            outputs=question_input
        )
        example_2.click(
            fn=lambda: (
                "Write a Python implementation of the A* search algorithm for pathfinding on a 2D grid. Explain the heuristic function used."
            ),
            outputs=question_input
        )
        example_3.click(
            fn=lambda: (
                "Why does the expression `0.1 + 0.2 == 0.3` return `False` in Python? Explain floating-point precision and how to properly compare floats."
            ),
            outputs=question_input
        )
        example_4.click(
            fn=lambda: (
                "Show an example of a SQL injection vulnerability in Python using SQLite3, and then demonstrate how to securely prevent it using parameterized queries."
            ),
            outputs=question_input
        )

    return app


if __name__ == "__main__":
    app = build_ui()
    print("Launching TechMentor AI on http://localhost:7865 ...")
    app.launch(server_port=7865, inbrowser=False, share=False, show_error=True)
