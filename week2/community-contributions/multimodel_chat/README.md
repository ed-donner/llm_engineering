# Multi-Model Chat Notebook

This folder contains a community contribution: a Gradio-based multimodel chat notebook that connects to a local Ollama server through the OpenAI Python SDK. It demonstrates how to build a local chat application with model selection, streaming responses, and a polished Gradio interface.

## What the notebook does

The notebook demonstrates how to build a local AI chat application that can switch between models at runtime. It uses:

- `OpenAI` with `base_url="http://localhost:11434/v1"` to communicate with Ollama
- `requests` to verify that the Ollama server is reachable
- `gradio` to build the user interface
- a `system_message` prompt to define assistant behavior
- a streaming `chat` callback so responses appear incrementally

The notebook is organized into the following steps:

1. Import the required libraries.
2. Check that Ollama is running locally.
3. Configure the OpenAI-compatible Ollama client.
4. Define the system prompt and model list.
5. Implement a streaming chat callback.
6. Build a Gradio `Blocks` interface with model selection, chat history, message input, and controls.
7. Launch the interface with `share=True`.

## Requirements

The notebook expects the following to be available:

- Python 3.11+
- a working local Ollama installation
- the models used in the notebook pulled into Ollama
- the Python packages listed in the repository environment file, including `openai`, `gradio`, and `requests`

If you are using the repository environment file, the recommended setup is:

```bash
conda env create -f environment.yml
conda activate llms
```

## How to run

1. Start Ollama in a terminal:

```bash
ollama serve
```

2. Make sure the models used in the notebook are installed:

```bash
ollama pull llama3.2
ollama pull gpt-oss:20b
```

3. Open `week2_practice.ipynb` in Jupyter or VS Code.

4. Run the cells in order.

5. Execute the final Gradio cell to launch the interface.

The final UI cell launches with `share=True`, so Gradio will create a public link. If you only want a local-only app, change the launch call to `beautiful_demo.launch(share=False)` before running it.

## Implementation notes

- The chat function streams tokens as they are generated.
- The model dropdown allows runtime switching between available Ollama models.
- Chat history is preserved in Gradio message format and passed back into the model on each turn.
- The final interface uses a styled `Blocks` layout for a cleaner presentation.

## Troubleshooting

- If the notebook cannot reach Ollama, confirm `ollama serve` is running and check `http://localhost:11434/` in a browser.
- If a model is unavailable, pull it again with `ollama pull <model-name>`.
- If the Gradio share link does not appear, verify that outbound network access is allowed in your environment.
