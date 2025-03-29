import gradio as gr

# Define custom CSS with dark theme fixes, updated to use html.dark
custom_css = """
/* Root variables for light theme */
:root {
    --background: #ffffff;
    --secondary-background: #f7f7f7;
    --tertiary-background: #f0f0f0;
    --text: #000000;
    --secondary-text: #5d5d5d;
    --border: #e0e0e0;
    --accent: #ff7b2c;
    --accent-hover: #ff6a14;
    --button-text: #ffffff;
    --code-bg: #f7f7f7;
    --code-text: #000000;
    --dropdown-bg: #ffffff;
    --slider-track: #e0e0e0;
    --slider-thumb: #ff7b2c;
    --collapsible-header: #f0f0f0;
    --primary-button-bg: #4a6ee0;  /* Blue */
    --primary-button-hover: #3a5ec8;
    --secondary-button-bg: #444444;
    --secondary-button-hover: #555555;
    --danger-button-bg: #e74c3c;  /* Red */
    --danger-button-hover: #c0392b;
    --success-button-bg: #e67e22;  /* Orange */
    --success-button-hover: #d35400;
}

/* Dark theme variables using html.dark */
html.dark {
    --background: #1a1a1a;
    --secondary-background: #252525;
    --tertiary-background: #2a2a2a;
    --text: #ffffff;
    --secondary-text: #cccccc;
    --border: #444444;
    --accent: #ff7b2c;
    --accent-hover: #ff6a14;
    --button-text: #ffffff;
    --code-bg: #252525;
    --code-text: #ffffff;
    --dropdown-bg: #2a2a2a;
    --slider-track: #444444;
    --slider-thumb: #ff7b2c;
    --collapsible-header: #333333;
    --primary-button-bg: #4a6ee0;
    --primary-button-hover: #3a5ec8;
    --secondary-button-bg: #444444;
    --secondary-button-hover: #555555;
    --danger-button-bg: #e74c3c;
    --danger-button-hover: #c0392b;
    --success-button-bg: #e67e22;
    --success-button-hover: #d35400;
}

/* Base styles */
body {
    background-color: var(--background) !important;
    color: var(--text) !important;
    transition: all 0.3s ease;
}

.gradio-container {
    background-color: var(--background) !important;
    max-width: 100% !important;
}

/* Headers */
h1, h2, h3, h4, h5, h6, .gr-header {
    color: var(--text) !important;
}

/* Panels and blocks */
.gr-panel, .gr-form, .gr-box, .gr-block {
    background-color: var(--secondary-background) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
    border-radius: 6px !important;
}

/* Validation messages section */
.gr-accordion .gr-panel {
    background-color: var(--secondary-background) !important;
    color: var(--text) !important;
    border-color: #e74c3c !important; /* Red border */
}

.gr-accordion-header {
    background-color: var(--collapsible-header) !important;
    color: var(--text) !important;
}

/* Code editors */
.codebox, .code-editor, .cm-editor {
    background-color: var(--code-bg) !important;
    color: var(--code-text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
}

/* Syntax highlighting */
.cm-editor .cm-content, .cm-editor .cm-line {
    color: var(--code-text) !important;
}
.cm-editor .cm-keyword { color: #ff79c6 !important; } /* Pink */
.cm-editor .cm-number { color: #bd93f9 !important; }  /* Purple */
.cm-editor .cm-string { color: #f1fa8c !important; }  /* Yellow */
.cm-editor .cm-comment { color: #6272a4 !important; } /* Gray */

/* Buttons */
.gr-button {
    background-color: var(--tertiary-background) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
    border-radius: 4px !important;
}
.gr-button.success {
    background-color: var(--success-button-bg) !important;
    color: var(--button-text) !important;
}
.gr-button.success:hover {
    background-color: var(--success-button-hover) !important;
}
.gr-button.danger {
    background-color: var(--danger-button-bg) !important;
    color: var(--button-text) !important;
}
.gr-button.danger:hover {
    background-color: var(--danger-button-hover) !important;
}
.gr-button.secondary {
    background-color: var(--secondary-button-bg) !important;
    color: var(--button-text) !important;
}
.gr-button.secondary:hover {
    background-color: var(--secondary-button-hover) !important;
}

/* File upload */
.gr-file, .gr-file-upload {
    background-color: var(--secondary-background) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
}

/* Dropdowns */
.gr-dropdown, .gr-dropdown-container, .gr-dropdown select, .gr-dropdown option {
    background-color: var(--dropdown-bg) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
}

/* Slider */
.gr-slider {
    background-color: var(--background) !important;
}
.gr-slider-track {
    background-color: var(--slider-track) !important;
}
.gr-slider-handle {
    background-color: var(--slider-thumb) !important;
}
.gr-slider-value {
    color: var(--text) !important;
}

/* Code output */
.gr-code {
    background-color: var(--code-bg) !important;
    color: var(--code-text) !important;
    border-color: var(--border) !important;
}

/* Footer */
.footer {
    color: var(--secondary-text) !important;
}
.footer a {
    color: var(--accent) !important;
}
"""

# JavaScript for theme toggling and initialization
js_code = """
<script>
function toggleTheme(theme) {
    var url = new URL(window.location.href);
    if (theme === "dark") {
        url.searchParams.set('__theme', 'dark');
    } else {
        url.searchParams.delete('__theme');
    }
    window.location.href = url.href;
}

// Set the radio button based on current theme
document.addEventListener('DOMContentLoaded', function() {
    var urlParams = new URLSearchParams(window.location.search);
    var currentTheme = urlParams.get('__theme');
    if (currentTheme === 'dark') {
        document.querySelector('#theme_radio_container input[value="dark"]').checked = true;
    } else {
        document.querySelector('#theme_radio_container input[value="light"]').checked = true;
    }
});
</script>
"""

# Language and model options
INPUT_LANGUAGES = ["Python", "JavaScript", "Java", "TypeScript", "Swift", "C#", "Ruby", "Go", "Rust", "PHP"]
OUTPUT_LANGUAGES = ["Python", "JavaScript", "Java", "TypeScript", "Swift", "C#", "Ruby", "Go", "Rust", "PHP", "Julia"]
MODELS = ["GPT", "Claude", "CodeLlama", "Llama", "Gemini"]
DOC_STYLES = ["standard", "detailed", "minimal"]

# Build the interface
with gr.Blocks(css=custom_css, theme=gr.themes.Base()) as demo:
    # Inject the JavaScript code
    gr.HTML(js_code)
    
    # States for dynamic button text
    input_lang_state = gr.State("Python")
    output_lang_state = gr.State("JavaScript")
    
    # Header
    with gr.Row(elem_classes="header-container"):
        gr.HTML("<h1 class='header-title'>AI CodeXchange</h1>")
        # Theme selection radio and apply button
        theme_radio = gr.Radio(["light", "dark"], label="Theme", elem_id="theme_radio_container", value="dark")
        theme_button = gr.Button("Apply Theme")
    
    # Validation Messages
    with gr.Accordion("Validation Messages", open=True):
        with gr.Row():
            with gr.Column():
                input_code = gr.Code(language="python", label="Code In", lines=15, elem_classes="code-container")
            with gr.Column():
                output_code = gr.Code(language="javascript", label="Converted Code", lines=15, elem_classes="code-container")
    
    # Configuration Options
    with gr.Row():
        input_lang = gr.Dropdown(INPUT_LANGUAGES, label="Code In", value="Python")
        output_lang = gr.Dropdown(OUTPUT_LANGUAGES, label="Code Out", value="JavaScript")
        model = gr.Dropdown(MODELS, label="Model", value="GPT")
        temperature = gr.Slider(minimum=0, maximum=1, step=0.1, value=0.7, label="Temperature")
    
    # Document Options
    with gr.Row():
        document_check = gr.Checkbox(label="Document", value=True)
        doc_style = gr.Dropdown(DOC_STYLES, label="Document Style", value="standard")
    
    # File Upload
    with gr.Accordion("Upload", open=True):
        file_upload = gr.File(label="Drop File Here - or - Click to Upload")
    
    # Action Buttons
    with gr.Row(elem_classes="button-row"):
        convert_btn = gr.Button("Convert", elem_classes="success")
        clear_btn = gr.Button("Clear All", elem_classes="danger")
    
    # Run Buttons
    with gr.Row(elem_classes="button-row"):
        run_source = gr.Button("Run Source Code", elem_classes="secondary")
        run_target = gr.Button("Run Target Code", elem_classes="secondary")
    
    # Results
    with gr.Row():
        source_result = gr.Code(label="Source Code Result", language="python", lines=10, elem_classes="code-container")
        target_result = gr.Code(label="Converted Code Result", language="javascript", lines=10, elem_classes="code-container")
    
    # Download
    with gr.Accordion("Download", open=True):
        with gr.Row():
            dl_source = gr.Button("Download Source Code")
            dl_target = gr.Button("Download Converted Code")
    
    # Footer
    with gr.Row(elem_classes="footer"):
        gr.HTML("<div>Use via API</div><div>•</div><div>Built with Gradio</div><div>•</div><div>Settings</div>")
    
    # Theme toggle event
    theme_button.click(
        fn=None,
        inputs=None,
        outputs=[],
        js="""
        var theme = document.querySelector('#theme_radio_container input:checked').value;
        toggleTheme(theme);
        """
    )
    
    # Existing event handlers
    def convert_code(input_code, in_lang, out_lang, model, temp, doc, doc_style):
        return f"// Converted from {in_lang} to {out_lang} using {model}\n// Temperature: {temp}\n// Documentation: {doc} ({doc_style if doc else 'N/A'})"
    
    convert_btn.click(fn=convert_code, inputs=[input_code, input_lang_state, output_lang_state, model, temperature, document_check, doc_style], outputs=[output_code])
    
    def update_convert_btn_text(in_lang, out_lang):
        return f"Convert {in_lang} to {out_lang}", in_lang, out_lang
    
    input_lang.change(fn=update_convert_btn_text, inputs=[input_lang, output_lang], outputs=[convert_btn, input_lang_state, output_lang_state])
    output_lang.change(fn=update_convert_btn_text, inputs=[input_lang, output_lang], outputs=[convert_btn, input_lang_state, output_lang_state])
    
    def update_run_btn_text(in_lang, out_lang):
        return f"Run {in_lang}", f"Run {out_lang}"
    
    input_lang.change(fn=update_run_btn_text, inputs=[input_lang, output_lang], outputs=[run_source, run_target])
    output_lang.change(fn=update_run_btn_text, inputs=[input_lang, output_lang], outputs=[run_source, run_target])
    
    def clear_all():
        return "", "", "", ""
    
    clear_btn.click(fn=clear_all, inputs=[], outputs=[input_code, output_code, source_result, target_result])
    
    def run_code(code, lang):
        return f"// Running {lang} code...\n// Results would appear here"
    
    run_source.click(fn=run_code, inputs=[input_code, input_lang_state], outputs=[source_result])
    run_target.click(fn=run_code, inputs=[output_code, output_lang_state], outputs=[target_result])
    
    def handle_file_upload(file):
        if file is None:
            return ""
        with open(file.name, "r") as f:
            return f.read()
    
    file_upload.change(fn=handle_file_upload, inputs=[file_upload], outputs=[input_code])

if __name__ == "__main__":
    demo.launch()