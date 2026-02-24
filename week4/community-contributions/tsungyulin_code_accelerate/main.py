import dotenv
import os
from openai import OpenAI
from anthropic import Anthropic
import gradio as gr

# from .config import *

OPENAI_MODEL = "gpt-4o-mini"
CLAUDE_MODEL = "claude-3-5-haiku-20241022"

OUTPUT_MAX_TOKEN = 2000

CSS = """
    body {
        background: #f4f6fa;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }

    .raw textarea {
        border: 1.5px solid #00FFBF !important;
        box-shadow: 0 0 10px rgba(229, 115, 115, 0.3);
        color: #00FFBF !important;
        font-size: 24px;
    }

    .optimize textarea {
        border: 1.5px solid #FFBF00 !important;
        box-shadow: 0 0 10px rgba(129, 199, 132, 0.3);
        color: #FFBF00 !important;
        font-size: 24px
    }

    button {
        background: linear-gradient(90deg, #2196f3, #00BFFF);
        color: white !important;
        font-weight: bold;
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out;
    }

    button:hover {
        background: linear-gradient(90deg, #21cbf3, #2196f3);
        transform: scale(1.05);
    }

    h1 {
        text-align: center;
        color: #1565c0;
        font-size: 38px;
    }
    """

PYTHON_CODE = '''
import math

def pairwise_distance(points_a, points_b):
    """
    Compute the pairwise Euclidean distance between two sets of 3D points.

    Args:
        points_a: list of (x, y, z)
        points_b: list of (x, y, z)
    Returns:
        A 2D list of shape (len(points_a), len(points_b)) representing distances
    """
    distances = []
    for i in range(len(points_a)):
        row = []
        for j in range(len(points_b)):
            dx = points_a[i][0] - points_b[j][0]
            dy = points_a[i][1] - points_b[j][1]
            dz = points_a[i][2] - points_b[j][2]
            d = math.sqrt(dx * dx + dy * dy + dz * dz)
            row.append(d)
        distances.append(row)
    return distances


# Example usage
if __name__ == "__main__":
    import random
    points_a = [(random.random(), random.random(), random.random()) for _ in range(100)]
    points_b = [(random.random(), random.random(), random.random()) for _ in range(100)]
    dists = pairwise_distance(points_a, points_b)
    print(f"Distance[0][0] = {dists[0][0]:.4f}")
'''


def main():
    dotenv.load_dotenv(override=True)
    os.environ['OPENAI_API_KEY'] = os.getenv(
        'OPENAI_API_KEY', 'your-key-if-not-using-env')
    os.environ['ANTHROPIC_API_KEY'] = os.getenv(
        'ANTHROPIC_API_KEY', 'your-key-if-not-using-env')

    # codeReviser = CodeAccelerator('openai', os.getenv('OPENAI_API_KEY'))
    codeReviser = CodeAccelerator('anthropic', os.getenv('ANTHROPIC_API_KEY'))

    display_ui(codeReviser)


def safe_exec(code_str):
    import io
    import sys
    import time
    import ast
    # Build the buffer of IO to extract ouput of stdout
    stdout_buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_buffer

    try:
        tree = ast.parse(code_str)
        compiled = compile(tree, filename="<ast>", mode="exec")
        local_vars = {}
        start = time.time()
        exec(compiled, {}, local_vars)
        exec_time = time.time() - start
        print(f"This code spend {exec_time:.8f} seconds\n")

        # recover sys.stdout
        sys.stdout = old_stdout
        output_text = stdout_buffer.getvalue()
        return output_text

    except Exception as e:
        sys.stdout = old_stdout
        return f"Error: {e}"


def display_ui(codeReviser):
    def _optimize(pythonCode):
        for text in codeReviser.respond(pythonCode):
            yield text.replace("```python", "").replace("```", "")

    with gr.Blocks(css=CSS) as ui:
        gr.Markdown("# ✨Convert Python code for accelation")
        with gr.Row():
            beforeBlock = gr.Textbox(
                label="raw python code", value=PYTHON_CODE, lines=20, elem_classes=["raw"])
            afterBlock = gr.Textbox(
                label="optimized python code", lines=20, elem_classes=["optimize"])
        with gr.Row():
            convert = gr.Button("Convert code")
        with gr.Row():
            rawRunButton = gr.Button("Run raw code")
            optRunButton = gr.Button("Run optimized code")
        with gr.Row():
            rawOut = gr.TextArea(label="Raw result:",
                                 elem_classes=["raw"])
            optimizeOut = gr.TextArea(
                label="Optimize result:", elem_classes=["optimize"])

        convert.click(_optimize,
                      inputs=[beforeBlock], outputs=[afterBlock])
        rawRunButton.click(safe_exec, inputs=[beforeBlock], outputs=[rawOut])
        optRunButton.click(safe_exec, inputs=[
                           afterBlock], outputs=[optimizeOut])

    ui.launch(inbrowser=True)


class CodeAccelerator:

    def __init__(self, frontierModel: str, apiKey):
        self.frontierModel = frontierModel

        if frontierModel == "openai":
            self.llm = OpenAI(api_key=apiKey)
        elif frontierModel == "anthropic":
            self.llm = Anthropic(api_key=apiKey)
        else:
            raise ValueError(f'frontierModel {frontierModel} is invalid.')

    def _getChatTemplate(self, pythonCode):
        _code = pythonCode.strip()

        systemPrompt = '''
        You are an assistant that reimplements Python code in high performance and just spend the fastest possible time for an windows laptop.
        Respond only with Python code; use comments sparingly and do not provide any explanation other than occasional comments.
        The new Python code response needs to produce an identical output in the fastest possible time.
        '''
        userPrompt = f'''
        Rewrite this Python code with the fastest possible implementation that produces identical output in the least time.
        Respond only with Python code; do not explain your work other than a few comments.
        Remember to import all necessary python packages such as numpy.\n\n
        
        {_code}
        '''
        return [
            {"role": "system", "content": systemPrompt},
            {"role": "user", "content": userPrompt}
        ]

    def respond(self, pythonCode):
        """Generator"""
        chatTemplate = self._getChatTemplate(pythonCode)
        reply = ""
        if self.frontierModel == 'openai':
            stream = self.llm.chat.completions.create(messages=chatTemplate,
                                                      model=OPENAI_MODEL,
                                                      max_tokens=OUTPUT_MAX_TOKEN,
                                                      stream=True)
            for chunk in stream:
                chunkText = chunk.choices[0].delta.content or ""
                reply += chunkText
                yield reply
        elif self.frontierModel == "anthropic":
            stream = self.llm.messages.create(model=CLAUDE_MODEL,
                                              system=chatTemplate[0]['content'],
                                              messages=chatTemplate[1:],
                                              max_tokens=OUTPUT_MAX_TOKEN,
                                              stream=True)

            for chunk in stream:
                chunkText = chunk.delta.text if chunk.type == "content_block_delta" else ""
                reply += chunkText
                yield reply


if __name__ == "__main__":
    main()
