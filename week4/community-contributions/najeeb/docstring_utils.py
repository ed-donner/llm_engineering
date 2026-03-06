"""
Utilities for parsing Python source, finding undocumented targets, and inserting docstrings.
No LLM or API calls; used by the Auto-Docstring notebook/pipeline.
"""

import ast


# Step 2: Parse source
DOCSTRING_TARGETS = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def parse_source(source: str) -> ast.Module:
    """Parse Python source into an AST. Raises SyntaxError if invalid."""
    return ast.parse(source)


def get_docstring_targets(tree: ast.Module) -> list[ast.AST]:
    """Collect all nodes that can have docstrings (Module, ClassDef, FunctionDef, AsyncFunctionDef)."""
    return [node for node in ast.walk(tree) if isinstance(node, DOCSTRING_TARGETS)]


# Step 3: Find undocumented targets
def has_docstring(node: ast.AST) -> bool:
    """True if the node's first body statement is a docstring (Expr with Constant string)."""
    if not getattr(node, "body", None):
        return False
    first = node.body[0]
    return (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    )


def get_node_kind(node: ast.AST) -> str:
    """Map AST node type to 'module' | 'class' | 'function' | 'async function'."""
    return {
        ast.Module: "module",
        ast.ClassDef: "class",
        ast.FunctionDef: "function",
        ast.AsyncFunctionDef: "async function",
    }[type(node)]


def get_node_line(node: ast.AST) -> int:
    """Line number for display. Module has no lineno; use first body line or 1."""
    if isinstance(node, ast.Module):
        return node.body[0].lineno if node.body else 1
    return node.lineno


def get_snippet(lines: list[str], node: ast.AST, max_lines: int = 30) -> str:
    """Slice of source for this node (for LLM context). Module = top of file; others by lineno/end_lineno."""
    if isinstance(node, ast.Module):
        start, end = 0, min(max_lines, len(lines))
    else:
        start = node.lineno - 1
        end = min(getattr(node, "end_lineno", start + 1), start + max_lines)
    return "\n".join(lines[start:end])


def find_undocumented_targets(
    tree: ast.Module, source: str, max_snippet_lines: int = 30
) -> list[tuple[ast.AST, str, str, str]]:
    """List of (node, name, kind, snippet) for nodes that need a docstring."""
    lines = source.splitlines()
    targets = get_docstring_targets(tree)
    result = []
    for node in targets:
        if has_docstring(node):
            continue
        name = getattr(node, "name", "<module>")
        kind = get_node_kind(node)
        snippet = get_snippet(lines, node, max_snippet_lines)
        result.append((node, name, kind, snippet))
    return result


# Step 4: Reverse line order
def get_insert_line(node: ast.AST) -> int:
    """1-based line number where the docstring will be inserted (before first body statement)."""
    if not getattr(node, "body", None):
        return getattr(node, "lineno", 1)
    return node.body[0].lineno


def sort_targets_for_insertion(
    target_list: list[tuple[ast.AST, str, str, str]]
) -> list[tuple[ast.AST, str, str, str]]:
    """Sort (node, name, kind, snippet) by insert line descending for safe insertions."""
    return sorted(target_list, key=lambda item: get_insert_line(item[0]), reverse=True)


# Step 6: Insert docstrings
def get_indent_for_node(lines: list[str], node: ast.AST) -> str:
    """Leading whitespace of the node's first body line."""
    if not getattr(node, "body", None):
        return ""
    first_lineno = node.body[0].lineno
    line = lines[first_lineno - 1]
    return line[: len(line) - len(line.lstrip())]


def format_docstring_block(indent: str, doc_text: str) -> list[str]:
    """Turn raw docstring text into lines with indent and triple quotes."""
    doc_text = doc_text.strip()
    doc_lines = doc_text.splitlines()
    if len(doc_lines) <= 1:
        return [f'{indent}"""{(doc_lines[0] if doc_lines else doc_text)}"""']
    return [f'{indent}"""'] + [f"{indent}{line}" for line in doc_lines] + [f'{indent}"""']


def insert_docstring_into_lines(
    lines: list[str], insert_at_0based: int, indent: str, doc_text: str
) -> None:
    """Insert the docstring block at the given 0-based line index (in place)."""
    block = format_docstring_block(indent, doc_text)
    for i, line in enumerate(block):
        lines.insert(insert_at_0based + i, line)
