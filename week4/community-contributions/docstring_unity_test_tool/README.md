
# Docstring & Unit Test Generator

This is a copy of the repository https://github.com/Jsrodrigue/docstring_unity_test_generator.

---

Automate docstring and unit test creation for Python projects using LLMs. Provides both a CLI and a web UI so teams can quickly increase documentation quality and test coverage with minimal manual work.


## Features
- Safe docstring insertion (Injects only the docstring)
- Mirrors your project tree into `tests/` and creates pytest-style test files.
- CLI (Typer) + Web UI (Gradio).
- Modular LLM execution layer; swap or add models easily.
- Configurable: select models and specific functions/classes.

## Why it matters
- Save developer time by auto-creating high-quality docstrings.
- Produce realistic unit tests that mirror your project structure.
- Keep your codebase well-documented and more maintainable, accelerating onboarding and code reviews.


## Screenshots

<p align="center">
  <img src="screenshots/docstring_ui.png" alt="Docstring UI" width="750" />
  <br/>
  <strong>Screenshot of the Docstring Interface</strong>
</p>

---

<p align="center">
  <img src="screenshots/test_ui.png" alt="Test UI" width="750" />
  <br/>
  <strong>Screenshot of the Test Interface</strong>
</p>

## Demo video for CLI usage

<p align="center">
  <a href="https://youtu.be/4-6kulni4_Y" target="_blank">
    <img src="https://img.youtube.com/vi/4-6kulni4_Y/maxresdefault.jpg" alt="Demo video for CLI usage" width="450" />
  </a>
  <br/>
  <strong>Click the image to watch a short demo of the CLI on YouTube</strong>
</p>

## Quick demo
Run the web UI:
```bash
python app_gradio.py
```

Generate docstrings from the CLI:
```bash
python -m src.cli docstring generate <folder_path> 
```

Generate unit tests:
```bash
python -m src.cli unit_test generate <folder_path> <project_path>
```
## CLI Usage
Run tools as Python modules:
---

###  Docstring Generator

```python
python -m src.cli docstring generate <path> [options]
```


**Options**
| Option | Description |
|---------|--------------|
| `<path>` | File or folder to scan. |
| `--model, -m` | Model to use (default: `gpt-4o-mini`). |
| `--names, -n` | Comma-separated list of names to process. |
| `--project, -p` | Root path of the project for indexing. |

**Example**
```python
python -m src.cli docstring generate src/utils -m openai/gpt-oss-120b
```


---

### Unit Test Generator
```python 
python -m src.cli unit_test generate <path> <project_path> [options]
```

**Options**
| Option | Description |
|---------|--------------|
| `<path>` | File or folder to analyze. |
| `<project_path>` | Root path of the project. |
| `--model, -m` | Model to use (default: `openai/gpt-oss-120b`). |
| `--names, -n` | Specific function/class names. |

**Example**
```python 
python -m src.cli unit_test generate src/utils /home/user/project -n add,subtract
```



## Inspiration & Educational Context

This project was inspired by the **Udemy course "AI Engineer Core Track: LLM Engineering, RAG, QLoRA, Agents" by Ed Donner**.  
It was developed as a **portfolio project** to demonstrate practical skills in LLM-based automation, agent design, and prompt engineering.  
The implementation uses **only the official OpenAI SDK**, showcasing a low-dependency, clean, and extensible approach to integrating language models into developer tools.

## Installation

Unix / macOS:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If you prefer the `pyproject.toml` workflow, you can also use `uv`.

### API Keys & Supported Models

This tool supports multiple LLM providers. You'll need to set up API keys in your environment:
```bash
OPENAI_API_KEY=your-key-here    # For gpt-4o-mini
GROQ_API_KEY=your-key-here      # For Llama and GPT-OSS models
```

Supported models:
- OpenAI: `gpt-4o-mini`
- Groq: 
  - `meta-llama/llama-4-scout-17b-16e-instruct`
  - `openai/gpt-oss-20b`
  - `openai/gpt-oss-120b`

Select models via `--model` flag in CLI or environment variables. 

The selection of models can be easily customizable by modifing the `constants.py` file.


## How it works (high level)
1. Scanner: parses the codebase and finds functions/classes.
2. LLM agent: generates docstrings or test code using prompts. 
3. Writer: writes docstrings into each source file and generates mirrored test files under tests/.
## Agents & Pipelines

This project uses a modular agent architecture where agents process Python files one at a time and return structured items (list of `DocstringOutput` and `UnitTestOutput` objects) containing the generated content and metadata.

### Agent Types & Responsibilities

- **Docstring Agent** (single-agent flow)
  - Processes one file at a time using `CodeExtractorTool`
  - For each function/class found, generates a docstring following PEP 257 conventions.
  - Returns a list of `DocstringOutput` generated content.

- **Unit Test Pipeline** (two-agent flow: Generator → Reviewer)
  - Generator agent:
    - Processes one source file at a time
    - Returns test `UnitTestOutput` objects with generated pytest functions
    - Includes necessary imports and fixtures in metadata
  - Reviewer agent:
    - Takes the generated file content.
    - Validates tests, imports, and assertions
    - Returns fixed test code or validation report

### Processing Flow

1. IndexScanner finds Python files and extracts `CodeItem` objects
2. Agents process files one by one:
   ```
   module.py → [CodeItem1, CodeItem2, ...] → Generator → Reviewer → Final Items
   ```
3. Review (only for docstring) and write.


### Benefits of File-based Processing

- Granular control: accept/reject changes per function
- Better context: each item includes its imports and dependencies
- Efficient processing: only changed files are reprocessed
- Safe execution: process one file at a time, handle errors gracefully

### Configuration

- Models are configurable via CLI flags or in the gradio app.
- Each agent can use a different model (e.g., faster model for review)
- Processing can be parallelized across files (but serial within each file)

## Run tests
```bash
python -m pytest tests/
```

## Project structure (high level)
- `src/` — main implementation modules (CLI, generators, executors, agents).
- `examples/` — sample usage and quick demos.
- `tests/` — unit tests (auto-generated tests appear here).
- `app_gradio.py` — launch Gradio web UI.

## Indexing (ProjectIndexer)

This project includes an incremental project indexer that scans your Python codebase and extracts "code items" (functions, classes, imports, etc.) for fast lookup and context. The indexer is implemented in `src/core_base/indexer/project_indexer.py` and provides an efficient workflow for large repositories.

## License
This project is licensed under the MIT License — see the `LICENSE` file in this repository for details.

