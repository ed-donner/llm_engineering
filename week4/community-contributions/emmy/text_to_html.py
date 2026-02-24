import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

# --- Load environment keys ---
load_dotenv(override=True)
openai_api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

# --- Model config ---
MODEL_MAP = {
    "GPT-4o-mini": {
        "model": "gpt-4o-mini",
        "key": openai_api_key,
        "endpoint": "https://api.openai.com/v1"
    },
    "Gemini-Flash": {
        "model": "gemini-2.5-flash",
        "key": google_api_key,
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/"
    }
}

class PageBuilder:
    def __init__(self, model_choice="GPT-4o-mini"):
        self.set_model(model_choice)

    def set_model(self, model_choice: str):
        spec = MODEL_MAP[model_choice]
        self.client = OpenAI(
            api_key=spec["key"],
            base_url=spec["endpoint"]
        )
        self.model_name = spec["model"]

    def build_page(self, raw_text: str, theme: str) -> str:
        """
        Ask the model for a self-contained HTML page (HTML + <style>) that
        uses the exact user text as page content, styled according to theme.
        The model is NOT allowed to rewrite, shorten, or invent extra content.
        """

        system_prompt = f"""
You are a frontend designer.

Your job:
- Take the user's provided text content and wrap it in a beautiful, responsive, single-page website.
- DO NOT rewrite, summarize, or invent new content. Use their words exactly.
- You MAY break the text into sections/paragraph blocks and add headings ONLY if the headings are already strongly implied
  by phrases like "Summary:", "Problem:", "Conclusion:", etc.
- If there are no obvious headings, just present the content nicely in cards/sections.

Styling rules:
- The site must look modern and clean.
- Use semantic HTML5: <header>, <main>, <section>, <footer>.
- Include all CSS inside a single <style> tag in the same HTML so it's fully self-contained.
- Make the layout centered, with readable max-width, good spacing, soft rounded corners, and balanced typography.
- The theme to apply is: "{theme}".

Theme hints:
- "Minimal": grayscale, lots of whitespace, system fonts, light gray dividers.
- "Professional": light background, subtle border cards, maybe a soft accent color for headings.
- "Colorful": playful accent colors, maybe soft tinted section backgrounds.
- "Modern Gradient": nice hero header section with a gentle gradient background and rounded containers.

Output rules:
- Return ONLY valid HTML starting with <!DOCTYPE html> and nothing else.
- Do NOT wrap the HTML in Markdown fences.
        """.strip()

        user_prompt = f"""
Here is the user's raw text. Remember: do not change the wording, just present it beautifully.

USER_TEXT_START
{raw_text}
USER_TEXT_END
        """.strip()

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        html = response.choices[0].message.content.strip()

        if html.startswith("```"):
            html = html.strip("`")
            html = html.replace("html", "", 1).strip()
        if html.endswith("```"):
            html = html[:-3].strip()

        return html

def apply_readability_fix(html_page: str) -> str:
    """
    Ensures preview text is readable without destroying the design.
    Only targets text color and ensures sufficient contrast.
    """
    fix = """
    <style>
    /* Readability fixes for preview only */
    body {
        color: #1a1a1a !important;
    }
    p, li, span, div, td, th, blockquote {
        color: #2d2d2d !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #0a0a0a !important;
    }
    /* Ensure backgrounds aren't forcing white text */
    section, article, main {
        color: #2d2d2d !important;
    }
    /* Fix if text is set to white/very light */
    [style*="color: white"], [style*="color: #fff"], [style*="color: #ffffff"] {
        color: #2d2d2d !important;
    }
    </style>
    """
    return html_page.replace("</head>", fix + "\n</head>") if "</head>" in html_page else fix + html_page

def build_interface():
    with gr.Blocks(
        title="PrettyPage",
        theme=gr.themes.Soft(primary_hue="indigo", neutral_hue="slate")
    ) as demo:
        gr.Markdown(
            """
            <div style="text-align:center">
                <h1 style="margin-bottom:0.25rem;">✨ PrettyPage Generator</h1>
                <p style="font-size:0.9rem; color:gray;">
                    Paste any text. Get a clean, beautiful, responsive webpage using your exact words.
                </p>
            </div>
            """,
        )

        with gr.Row():
            model_choice = gr.Radio(
                choices=list(MODEL_MAP.keys()),
                value="GPT-4o-mini",
                label="Model",
                info="Which model should generate the page?"
            )
            theme_choice = gr.Dropdown(
                choices=[
                    "Minimal",
                    "Professional",
                    "Colorful",
                    "Modern Gradient"
                ],
                value="Professional",
                label="Style Theme",
                info="Controls colors / layout vibe"
            )

        input_text = gr.Textbox(
            label="Your Text Content",
            lines=12,
            placeholder=(
                "Paste your notes, article, README, sales copy, lesson, etc.\n"
                "We'll turn this into a styled webpage without changing your words."
            ),
        )

        generate_btn = gr.Button("🎨 Generate Page", variant="primary")

        gr.Markdown("---")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("**Generated HTML (copy & save as .html):**")
                html_code_output = gr.Textbox(
                    label="HTML Source",
                    interactive=False,
                    lines=20,
                    max_lines=20,
                    show_copy_button=True
            )

            with gr.Column(scale=1):
                gr.Markdown("**Live Preview:**")
                live_preview = gr.HTML(
                    value=(
                        "<div style='color:gray;font-family:sans-serif;"
                        "padding:1rem;border:1px solid #ddd;border-radius:8px;'>"
                        "Your page preview will appear here.</div>"
                    ),
                )

        # click handler: build the page fresh each time
        def handle_generate(user_text, chosen_model, chosen_theme):
            porter = PageBuilder(chosen_model)
            html_page = porter.build_page(user_text, chosen_theme)
            fixed_preview = apply_readability_fix(html_page)
            # left pane shows code, right pane renders preview
            return html_page, fixed_preview

        generate_btn.click(
            fn=handle_generate,
            inputs=[input_text, model_choice, theme_choice],
            outputs=[html_code_output, live_preview],
        )

        gr.Markdown(
            """
            <div style="text-align:center; font-size:0.8rem; color:gray; margin-top:2rem;">
                Tip: Save the HTML Source above as <code>index.html</code> and open it in your browser.
            </div>
            """
        )

    return demo

if __name__ == "__main__":
    demo = build_interface()
    demo.launch(inbrowser=True)
