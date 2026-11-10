#.\.venv\Scripts\Activate.ps1
import os
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

openrouter_key = os.getenv("OPENROUTER_API_KEY")
openrouter_client = OpenAI(api_key=openrouter_key, base_url="https://openrouter.ai/api/v1") if openrouter_key else None

LANGUAGES = ["Python", "Java", "C++", "C"]
MODELS = {
    "Llama 3.1 8B (OpenRouter - Free)": {"client": openrouter_client, "id": "meta-llama/llama-3.1-8b-instruct:free"},
    "Nemotron 3 Ultra (OpenRouter - Free)": {"client": openrouter_client, "id": "nvidia/nemotron-3-ultra-550b-a55b:free"},
    "GLM 5.3 Flash (OpenRouter)": {"client": openrouter_client, "id": "z-ai/glm-5.3-flash"}
}

def translate_code(source_code, source_lang, target_lang, model_choice):
    if not source_code.strip():
        yield "⚠️ Please enter some code to translate."
        return

    if source_lang == target_lang:
        yield "⚠️ Source and target languages are the same."
        return

    model_info = MODELS.get(model_choice)
    if not model_info or not model_info["client"]:
        yield f"⚠️ API key for {model_choice} is missing. Please check your `.env` file."
        return

    client = model_info["client"]
    model_id = model_info["id"]

    system_prompt = (
        f"You are an expert software engineer specializing in {source_lang} and {target_lang}. "
        f"Translate the following {source_lang} code into idiomatic, highly optimized {target_lang} code. "
        "Return ONLY the translated code inside a markdown code block. Do not include any other text, pleasantries, or explanations."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": source_code}
    ]

    try:
        stream = client.chat.completions.create(
            model=model_id,
            messages=messages,
            stream=True,
            temperature=0.2
        )
        
        result = ""
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                result += chunk.choices[0].delta.content
                yield result
    except Exception as e:
        yield f"An error occurred during translation:\n```\n{str(e)}\n```"

# Custom CSS for a sleek, modern premium look
css = """
.main-container { max-width: 1200px; margin: 0 auto; padding-top: 20px; }
.header { text-align: center; margin-bottom: 25px; padding: 25px; background: linear-gradient(135deg, #1e293b, #0f172a); border-radius: 12px; color: white; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
.header h1 { font-weight: 800; font-size: 2.5em; margin-bottom: 0.1em; color: white; }
.header p { color: #94a3b8; font-size: 1.1em; }
.code-container { border-radius: 12px; overflow: hidden; }
"""

with gr.Blocks() as app:
    with gr.Column(elem_classes=["main-container"]):
        with gr.Column(elem_classes=["header"]):
            gr.Markdown("# 🔄 Universal Code Translator")
            gr.Markdown("Seamlessly translate logic between **Python**, **Java**, **C++**, and **C** using frontier AI models.")
        
        with gr.Row():
            with gr.Column(scale=1):
                model_dropdown = gr.Dropdown(
                    choices=list(MODELS.keys()),
                    value=list(MODELS.keys())[0],
                    label="🧠 AI Model Engine",
                    info="Select the model for translation"
                )
            with gr.Column(scale=1):
                source_lang = gr.Dropdown(
                    choices=LANGUAGES,
                    value="Python",
                    label="📝 Source Language"
                )
            with gr.Column(scale=1):
                target_lang = gr.Dropdown(
                    choices=LANGUAGES,
                    value="C++",
                    label="🎯 Target Language"
                )
        
        with gr.Row():
            with gr.Column(elem_classes=["code-container"]):
                source_code = gr.Code(
                    label="Source Code",
                    language="python",
                    lines=18
                )
            with gr.Column():
                target_code = gr.Markdown(
                    label="Translated Code (Streaming)",
                    value="*Your translation will appear here in real-time...*"
                )
                
        translate_btn = gr.Button("🚀 Translate Code", variant="primary", size="lg")
        
        # Example snippets for quick testing
        gr.Examples(
            examples=[
                ["def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)", "Python", "Java", "Llama 3.1 8B (OpenRouter - Free)"],
                ["int factorial(int n) {\n    if (n == 0) return 1;\n    return n * factorial(n - 1);\n}", "C", "Python", "Nemotron 3 Ultra (OpenRouter - Free)"],
                ["class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None", "Python", "C++", "GLM 5.3 Flash (OpenRouter)"]
            ],
            inputs=[source_code, source_lang, target_lang, model_dropdown]
        )

        # Dynamic syntax highlighting based on dropdown
        def update_syntax(lang):
            mapping = {"Python": "python", "Java": "java", "C++": "cpp", "C": "c"}
            return gr.Code(language=mapping.get(lang, "python"))

        source_lang.change(fn=update_syntax, inputs=[source_lang], outputs=[source_code])

        translate_btn.click(
            fn=translate_code,
            inputs=[source_code, source_lang, target_lang, model_dropdown],
            outputs=[target_code]
        )

if __name__ == "__main__":
    # Launch on a fresh port and open directly in the browser
    print("Launching AI Code Translator in your browser...")
    app.launch(server_port=7871, inbrowser=True, share=False, css=css, theme=gr.themes.Soft(primary_hue="indigo"))
