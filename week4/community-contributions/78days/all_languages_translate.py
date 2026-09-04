import os
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # loads .env file

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY")
)

LANGUAGES = [
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go",
    "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "SQL", "Bash"
]

SYSTEM_PROMPT = """You are an expert software engineer and code translator.
Your task is to accurately translate the given source code from one programming language to another.

Rules:
- Preserve the original logic, structure, and functionality as closely as possible.
- Use idiomatic code in the target language.
- Keep comments and translate them when appropriate.
- If something cannot be translated cleanly, add a clear comment explaining why.
- Only return the translated code. Do not wrap it in markdown code fences unless the user asks.
- Do not add any explanations outside the code."""

def translate_code(source_code: str, source_lang: str, target_lang: str, extra_instructions: str = ""):
    if not source_code.strip():
        yield "Please enter some code to translate."
        return

    user_content = f"""Translate the following {source_lang} code to {target_lang}.

{extra_instructions.strip() if extra_instructions else ""}

Source code:
```{source_lang.lower()}
{source_code}
```"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]

    try:
        stream = client.chat.completions.create(
            model="openai/gpt-oss-120b",  # excellent free model on Groq
            messages=messages,
            temperature=0.0,
            stream=True
        )

        partial = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            partial += delta
            yield partial

    except Exception as e:
        yield f"Error: {str(e)}"


with gr.Blocks(title="Code Translator", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🔄 AI Code Translator\nTranslate code between programming languages")

    with gr.Row():
        source_lang = gr.Dropdown(LANGUAGES, value="Python", label="From")
        target_lang = gr.Dropdown(LANGUAGES, value="JavaScript", label="To")

    with gr.Row():
        with gr.Column():
            source_code = gr.Code(label="Source Code", language="python", lines=18)
        with gr.Column():
            translated_code = gr.Code(label="Translated Code", language="javascript", lines=18)

    extra = gr.Textbox(
        label="Extra instructions (optional)",
        placeholder="e.g. Use modern ES6+ syntax, keep all comments..."
    )

    translate_btn = gr.Button("Translate →", variant="primary")

    # Update syntax highlighting
    source_lang.change(
        fn=lambda lang: gr.update(language=lang.lower() if lang.lower() in 
            ["python","javascript","typescript","java","c","cpp","go","rust","ruby","php","swift","kotlin","scala","r","sql","bash"] else None),
        inputs=source_lang, outputs=source_code
    )
    target_lang.change(
        fn=lambda lang: gr.update(language=lang.lower() if lang.lower() in 
            ["python","javascript","typescript","java","c","cpp","go","rust","ruby","php","swift","kotlin","scala","r","sql","bash"] else None),
        inputs=target_lang, outputs=translated_code
    )

    translate_btn.click(
        fn=translate_code,
        inputs=[source_code, source_lang, target_lang, extra],
        outputs=translated_code
    )

if __name__ == "__main__":
    demo.launch()