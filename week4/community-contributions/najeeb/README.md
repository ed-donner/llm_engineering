# Auto-Docstring Tool (LLM-based)

Add PEP-257 docstrings to Python code using an LLM. Paste code or upload a `.py` file; choose docstring style (Google, NumPy, reStructuredText) and model; get back the same code with generated docstrings.

---

## Overview: Steps 1–7

| Step | What it does |
|------|----------------|
| **1. Setup** | Imports, load env, check API key, create LLM client, define `SYSTEM_PROMPT`. |
| **2. Parse source** | `ast.parse(source)` and collect nodes: Module, ClassDef, FunctionDef, AsyncFunctionDef. |
| **3. Find undocumented targets** | Keep only nodes without a docstring; for each get name, kind, and code snippet. |
| **4. Process in reverse line order** | Sort targets by insert line descending so insertions don’t shift line numbers. |
| **5. Call LLM** | Build user prompt (style, kind, name, snippet), call API, get docstring text for each target. |
| **6. Insert docstrings** | For each target: get indent, format docstring block, insert at the correct line (reverse order). |
| **7. Output** | Return the new source and count; optionally write to a file with `add_docstrings_to_file()`. |

---

## Step details

### Step 1: Setup

Load environment variables, check API key, create the LLM client (e.g. OpenRouter), and define the system prompt. The notebook keeps only the necessary code; run those cells in order so `openai`, `api_key`, and `SYSTEM_PROMPT` are available.

### Step 2: Parse source

- **Goal:** Turn the raw Python source into an AST and collect only the nodes that can have docstrings: the **module**, **classes**, and **functions** (including async).
- `ast.parse(source)` returns a `Module` node whose `body` is a list of statements.
- We walk the tree and keep every node whose type is one of: `Module`, `ClassDef`, `FunctionDef`, `AsyncFunctionDef`.
- Implementation lives in `docstring_utils.py`: `parse_source()`, `get_docstring_targets()`.

### Step 3: Find undocumented targets

- **Goal:** From the list of docstring-capable nodes, keep only those that **don’t already have** a docstring, and for each compute: **name**, **kind** (module/class/function/async function), and **snippet** (slice of source for the LLM).
- **How we detect “has docstring”:** In the AST, a docstring is the first statement in the body: an `Expr` node whose value is a `Constant` (string). If that’s present, we skip the node.
- **Snippet:** We slice source lines by `lineno`/`end_lineno` (capped, e.g. 30 lines) so the model sees the definition.
- Implementation: `has_docstring()`, `get_node_kind()`, `get_node_line()`, `get_snippet()`, `find_undocumented_targets()` in `docstring_utils.py`.

### Step 4: Process in reverse line order

- **Goal:** Sort the list of undocumented targets by **descending** line number (insert line). That way, when we insert a docstring at line 5, we don’t change the line numbers of the function at line 10.
- **Insertion line:** The docstring goes before the first statement of the node (e.g. `node.body[0].lineno`). We sort by this value descending.
- Implementation: `get_insert_line()`, `sort_targets_for_insertion()` in `docstring_utils.py`.

### Step 5: Call LLM (and user prompt)

- **Goal:** For each target, build the user message (style, kind, name, snippet), call the LLM with the system prompt, get back the docstring text only (no triple quotes).
- **User prompt template:**

  ```
  Write a {style}-style docstring for this Python {kind} '{name}':

  {snippet}
  ```

- **System prompt:** Instructs the model to output only the inner docstring content, follow the requested style, and not invent parameters or behavior.
- Implementation in notebook: `build_user_prompt()`, `ask_llm_for_docstring()`.

### Step 6: Insert docstrings into source

- **Goal:** For each target we have the node, the docstring text from the LLM, and the list of source lines. We compute the indent for that node, format the docstring as a block (triple quotes, correct indentation), and insert it at the correct 0-based line. Processing in reverse order keeps line numbers valid.
- Implementation: `get_indent_for_node()`, `format_docstring_block()`, `insert_docstring_into_lines()` in `docstring_utils.py`.

### Step 7: Full pipeline and output

- **Goal:** Parse → find undocumented → sort → for each target call LLM → insert docstring → return new source and count. Optionally write to a file.
- Implementation in notebook: `add_docstrings_to_source()`, `add_docstrings_to_file()`.

---

## Testing

- **Option A – Gradio:** Run the Gradio cell in the notebook. Paste code or upload a `.py` file, choose style and model, click **Add docstrings**.
- **Option B – Code:**  
  `new_source, count = add_docstrings_to_source(source, style="Google", model=openai_model, client=openai)`  
  Or for a file:  
  `add_docstrings_to_file("path/to/script.py", style="Google", out_path="path/to/output.py")`.

---

## Project layout

- **`week4_solution.ipynb`** – Setup, prompts, pipeline, and Gradio UI. Imports from `docstring_utils`; no AST/source logic duplicated.
- **`docstring_utils.py`** – All non-LLM code: AST parsing (Step 2), finding/sorting targets (Steps 3–4), and inserting docstrings (Step 6). Reusable and testable without an API key.
- **`README.md`** – This file (steps and usage).

---

## Requirements

- Python 3.10+
- `openai`, `gradio`, `python-dotenv`
- API key in `.env` (e.g. `OPENAI_API_KEY` for OpenRouter).
