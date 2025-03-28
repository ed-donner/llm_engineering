import gradio as gr

# JavaScript function to toggle theme
js_code = """
function toggleTheme(theme) {
    var url = new URL(window.location.href);
    if (theme === "dark") {
        url.searchParams.set('__theme', 'dark');
    } else {
        url.searchParams.delete('__theme');
    }
    window.location.href = url.href;
}
"""

def create_app():
    with gr.Blocks(js=js_code) as demo:
        theme_radio = gr.Radio(["light", "dark"], label="Theme")
        
        # Button to trigger the theme change
        theme_button = gr.Button("Toggle Theme")
        
        # Use JavaScript to toggle the theme when the button is clicked
        theme_button.click(
            None,
            inputs=[theme_radio],
            js=f"(theme) => {{ toggleTheme(theme); return []; }}",
            queue=False,
        )
        
    return demo

if __name__ == "__main__":
    app = create_app()
    app.launch()