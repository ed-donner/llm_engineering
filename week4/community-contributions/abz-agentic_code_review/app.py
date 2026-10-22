import gradio as gr
from dotenv import load_dotenv
from orchestrator import run_pipeline

load_dotenv(override=True)

# Sample input 
SAMPLE_CODE = '''def calculate_discount(price, discount_percent):
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    return price * (1 - discount_percent / 100)

def apply_tax(price, tax_rate=0.11):
    return price * (1 + tax_rate)

def final_price(price, discount_percent, tax_rate=0.11):
    discounted = calculate_discount(price, discount_percent)
    return apply_tax(discounted, tax_rate)
'''

# Pipeline runner for Gradio 
def run(python_code):
    log_lines = []
    documented_code = ""
    test_code = ""
    test_output = ""

    for item in run_pipeline(python_code):
        if isinstance(item, str):
            log_lines.append(item)
            yield (
                "\n".join(log_lines),
                documented_code,
                test_code,
                test_output
            )
        elif isinstance(item, dict):
            documented_code = item["documented_code"]
            test_code = item["test_code"]
            test_output = item["test_result"].output if item["test_result"] else ""
            yield (
                "\n".join(log_lines),
                documented_code,
                test_code,
                test_output
            )

# UI Layout 
with gr.Blocks(theme=gr.themes.Monochrome(), title="Agentic Code Hardening Pipeline") as ui:
    
    gr.Markdown("# Agentic Code Hardening Pipeline")
    gr.Markdown(
        "Paste Python code → AI will automatically: "
        "**① add docstrings** → **② generate unit tests** → **③ self-heal if tests fail**"
    )

    with gr.Row():
        with gr.Column(scale=1):
            python_input = gr.Code(
                label="Python Input",
                value=SAMPLE_CODE,
                language="python",
                lines=20
            )
            run_btn = gr.Button("▶ Run Pipeline", variant="primary", size="lg")

        with gr.Column(scale=1):
            agent_log = gr.Markdown(label="Agent Log", value="*The pipeline has not been run...*")

    with gr.Row():
        with gr.Column():
            documented_out = gr.Code(
                label="① Documented Code",
                language="python",
                lines=20
            )
        with gr.Column():
            test_out = gr.Code(
                label="② Generated Unit Tests",
                language="python",
                lines=20
            )

    with gr.Row():
        test_result_out = gr.Textbox(
            label="③ Test Results",
            lines=10,
            interactive=False
        )

    run_btn.click(
        fn=run,
        inputs=[python_input],
        outputs=[agent_log, documented_out, test_out, test_result_out]
    )

ui.launch(inbrowser=True)