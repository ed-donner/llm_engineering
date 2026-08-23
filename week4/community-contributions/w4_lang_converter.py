import os
import io
import sys
import re
import subprocess
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
import gradio as gr

# Load environment variables and initialize APIs
load_dotenv(override=True)
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MACHINE_SPEC = "MacbookPro, Apple M1 Chip"

# Define global variables for HF integration
# For HF chat-based CodeQwen model
code_qwen = "Qwen/CodeQwen1.5-7B-Chat"
CODE_QWEN_URL = ""


def clean_code(code, target_language):
    """
    Remove markdown code fences and stray language indicators.
    Also apply language-specific replacements.
    """
    raw_lines = code.splitlines()
    cleaned_lines = []
    for line in raw_lines:
        if "```" in line:
            continue
        if line.strip().lower() in ["c", "cpp", "c++", "rust"]:
            continue
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines)
    if target_language == "C":
        cleaned = cleaned.replace("1U << 32", "(1ULL << 32)")
    if target_language == "Rust":
        cleaned = process_rust_code(cleaned)
    return cleaned

# Conversion prompt functions (target language-aware)
def user_prompt_for(python_code, target_language):
    return (
        f"Rewrite this Python code in {target_language} with the fastest possible implementation that produces identical output. "
        f"Respond only with {target_language} code; do not explain your work. "
        "Pay attention to number types to ensure no int overflows. Remember to #include all necessary C++ packages such as iomanip.\n\n"
        + python_code
    )

def messages_for(python_code, target_language):
    system_message = (
        f"You are an assistant that reimplements Python code in high performance {target_language} for an {MACHINE_SPEC}. "
        f"Respond only with {target_language} code; use comments sparingly. "
        f"The {target_language} response needs to produce an identical output in the fastest possible time."
    )
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt_for(python_code, target_language)},
    ]

def write_output(code, target_language):
    """Write the converted code to a file based on target language."""
    tag = target_language.lower() if target_language is not None else ""
    if target_language == "C++":
        filename = "optimized.cpp"
    elif target_language == "C":
        filename = "optimized.c"
    elif target_language == "Rust":
        filename = "optimized.rs"
    else:
        filename = "optimized.txt"
    cleaned = code.replace(f"```{tag}\n", "").replace("```", "")
    lines = cleaned.splitlines()
    if lines and lines[0].strip().lower() in ["cpp", "c++", "c", "rust"]:
        lines = lines[1:]
    cleaned = "\n".join(lines)
    cleaned = clean_code(cleaned, target_language)
    with open(filename, "w") as f:
        f.write(cleaned)
    return filename

# GPT integration for conversion
def stream_gpt(python_code, target_language, model_version):
    stream = openai.chat.completions.create(
        model=model_version,  # Use selected GPT model version
        messages=messages_for(python_code, target_language),
        stream=True,
    )
    reply = ""
    for chunk in stream:
        if not hasattr(chunk, "choices") or not chunk.choices:
            continue
        fragment = chunk.choices[0].delta.content or ""
        reply += fragment
        yield reply.replace(f"```{target_language}\n", "").replace("```", "")

# Claude integration for conversion
def stream_claude(python_code, target_language, model_version):
    prompt = user_prompt_for(python_code, target_language)
    response = anthropic.completions.create(
        prompt=prompt,
        model=model_version,
        stream=True,
    )
    reply = ""
    for chunk in response:
        fragment = chunk.get("completion", "")
        reply += fragment
        yield reply.replace(f"```{target_language}\n", "").replace("```", "")

# Hugging Face integration functions
def stream_code_qwen(python_code, target_language, model_version):
    """
    HF chat-based model using CodeQwen.
    """
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(code_qwen)
    messages = messages_for(python_code, target_language)
    # Convert messages to chat format as expected by Qwen.
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    from huggingface_hub import InferenceClient
    client = InferenceClient(CODE_QWEN_URL, token=os.getenv("HF_TOKEN"))
    stream = client.text_generation(text, stream=True, details=True, max_new_tokens=3000)
    result = ""
    for r in stream:
        result += r.token.text
        yield result.replace(f"```{target_language}\n", "").replace("```", "")

def stream_huggingface(python_code, target_language, model_version):
    """
    HF single-prompt model integration.
    """
    prompt = user_prompt_for(python_code, target_language)
    from huggingface_hub import InferenceClient
    client = InferenceClient(model_name=model_version, token=os.getenv("HF_TOKEN"))
    stream = client.text_generation(prompt, stream=True, details=True, max_new_tokens=3000)
    reply = ""
    for chunk in stream:
        reply += chunk.token.text
        yield reply.replace(f"```{target_language}\n", "").replace("```", "")


def optimize(python_code, combined_model, target_language):
    """
    combined_model is a string like "GPT: gpt-4o", "CLAUDE: claude-3-5-sonnet-20240620" or "HF: model_name"
    """
    provider, model_version = [x.strip() for x in combined_model.split(":")]
    if provider == "GPT":
        for partial in stream_gpt(python_code, target_language, model_version):
            yield partial
    elif provider == "CLAUDE":
        for partial in stream_claude(python_code, target_language, model_version):
            yield partial
    elif provider == "HF":
        if "CodeQwen" in model_version:
            for partial in stream_code_qwen(python_code, target_language, model_version):
                yield partial
        else:
            for partial in stream_huggingface(python_code, target_language, model_version):
                yield partial
    else:
        raise ValueError("Unknown model provider")

def execute_python(code):
    """Execute Python code and return its output."""
    env = {}  # Dedicated global namespace
    try:
        output = io.StringIO()
        sys.stdout = output
        exec(code, env)
    finally:
        sys.stdout = sys.__stdout__
    return output.getvalue()

def execute_cpp(code):
    write_output(code, target_language="C++")
    try:
        compile_cmd = [
            "clang++", "-Ofast", "-std=c++17", "-march=armv8.5-a",
            "-mtune=apple-m1", "-mcpu=apple-m1", "-o", "optimized", "optimized.cpp"
        ]
        subprocess.run(compile_cmd, check=True, text=True, capture_output=True)
        run_cmd = ["./optimized"]
        run_result = subprocess.run(run_cmd, check=True, text=True, capture_output=True)
        return run_result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error:\n{e.stderr}"

def execute_c(code):
    cleaned_code = clean_code(code, "C")
    with open("optimized.c", "w") as f:
        f.write(cleaned_code)
    try:
        compile_cmd = ["clang", "-O2", "-std=c11", "-o", "optimized_c", "optimized.c"]
        subprocess.run(compile_cmd, check=True, text=True, capture_output=True)
        run_cmd = ["./optimized_c"]
        run_result = subprocess.run(run_cmd, check=True, text=True, capture_output=True)
        return run_result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error:\n{e.stderr}"

def process_rust_code(code):
    code = code.replace("{:.6f}", "{:.6}")
    code = re.sub(
        r'(println!$begin:math:text$"Execution Time: \\{\\:\\.6\\} seconds", duration\\.as_secs_f64)(\\s*)$',
        r'\\1())',
        code,
        flags=re.MULTILINE,
    )
    code = code.replace("max_val - min_val as u32 + 1", "((max_val - min_val + 1) as u32)")
    code = code.replace("1 << 32", "1u64 << 32")
    code = re.sub(r'($end:math:text$\s*as i64)\)', r'\1', code)
    return code

def execute_rust(code):
    code = code.replace("```rust\n", "").replace("```", "")
    lines = code.split('\n', 1)
    if lines and lines[0].strip().lower() == "rust":
        code = lines[1] if len(lines) > 1 else ""
    code = process_rust_code(code)
    with open("optimized.rs", "w") as f:
        f.write(code)
    try:
        compile_cmd = ["rustc", "optimized.rs", "-O", "-o", "optimized_rust"]
        subprocess.run(compile_cmd, check=True, text=True, capture_output=True)
        run_cmd = ["./optimized_rust"]
        run_result = subprocess.run(run_cmd, check=True, text=True, capture_output=True)
        return run_result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error:\n{e.stderr}"

def execute_target_code(code, target_language):
    """Select the appropriate execution function based on target language."""
    if target_language == "C++":
        return execute_cpp(code)
    elif target_language == "C":
        return execute_c(code)
    elif target_language == "Rust":
        return execute_rust(code)
    else:
        return "Unsupported language"

# Gradio UI setup
css = """
.python {background-color: #306998;}
.code {background-color: #050;}
"""

def launch_ui():
    with gr.Blocks(css=css) as ui:
        gr.Markdown("## Convert Python Code to C/C++/Rust")
        with gr.Row():
            python_box = gr.Textbox(label="Python code:", value=PYTHON_HARD, lines=10)
            converted_box = gr.Textbox(label="Converted Code:", lines=10)
        with gr.Row():
            model_dropdown = gr.Dropdown(
                ["GPT: gpt-4o", "GPT: gpt-4o-mini", "CLAUDE: claude-3-5-sonnet-20240620", "CLAUDE: claude-3-haiku-20240307", "HF: CodeQwen1.5-7B-Chat", "HF: bigcode/starcoder"],
                label="Select Model",
                value="GPT: gpt-4o"
            )
            target_lang_dropdown = gr.Dropdown(
                ["C++", "C", "Rust"],
                label="Select target language",
                value="C++"
            )
        with gr.Row():
            convert_btn = gr.Button("Convert code")
        with gr.Row():
            python_run_btn = gr.Button("Run Python")
            run_converted_btn = gr.Button("Run Converted Code")
        with gr.Row():
            python_out = gr.TextArea(label="Python result:", elem_classes=["python"])
            converted_out = gr.TextArea(label="Converted Code result:", elem_classes=["code"])
        convert_btn.click(
            optimize,
            inputs=[python_box, model_dropdown, target_lang_dropdown],
            outputs=[converted_box],
        )
        python_run_btn.click(execute_python, inputs=[python_box], outputs=[python_out])
        run_converted_btn.click(
            execute_target_code,
            inputs=[converted_box, target_lang_dropdown],
            outputs=[converted_out],
        )
    ui.launch()

# Example Python code blocks
PYTHON_HARD = """
# Support large number sizes
def lcg(seed, a=1664525, c=1013904223, m=2**32):
    value = seed
    while True:
        value = (a * value + c) % m
        yield value
def max_subarray_sum(n, seed, min_val, max_val):
    lcg_gen = lcg(seed)
    random_numbers = [next(lcg_gen) % (max_val - min_val + 1) + min_val for _ in range(n)]
    max_sum = float('-inf')
    for i in range(n):
        current_sum = 0
        for j in range(i, n):
            current_sum += random_numbers[j]
            if current_sum > max_sum:
                max_sum = current_sum
    return max_sum
def total_max_subarray_sum(n, initial_seed, min_val, max_val):
    total_sum = 0
    lcg_gen = lcg(initial_seed)
    for _ in range(20):
        seed = next(lcg_gen)
        total_sum += max_subarray_sum(n, seed, min_val, max_val)
    return total_sum
n = 10000
initial_seed = 42
min_val = -10
max_val = 10
import time
start_time = time.time()
result = total_max_subarray_sum(n, initial_seed, min_val, max_val)
end_time = time.time()
print("Total Maximum Subarray Sum (20 runs):", result)
print("Execution Time: {:.6f} seconds".format(end_time - start_time))
"""

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Single script with multiple executable sections and target language support"
    )
    parser.add_argument(
        "--mode",
        choices=["direct", "ui"],
        default="ui",
        help="Run direct conversion or launch Gradio UI",
    )
    args = parser.parse_args()

    if args.mode == "direct":
        print("\nExecuting Python code (PYTHON_HARD)...")
        exec(PYTHON_HARD)
        for partial in optimize(PYTHON_HARD, "GPT: gpt-4o", "C++"):
            print(partial, end="")
    elif args.mode == "ui":
        launch_ui()