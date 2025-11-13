
import ast
from pathlib import Path
from typing import List, Union, Optional
import sys
from src.core_base.code.code_model import CodeItem
from src.core_base.code.extractor_utils import _get_signature_from_node

class CodeExtractorTool:
    """
    Extracts Python functions, methods, and classes from source files or directories.
    
    This tool walks through the abstract syntax tree (AST) of each Python file to collect structured information about each code entity (function, method, or class), including its name, type, source code, docstring, file location, imports, and signature.
    """

    def __init__(self, base_path: Path):
        self.base_path = base_path.resolve()

    def _process_node(
        self, node: ast.AST,
        source_lines: List[str],
        file_path: Path,
        imports: List[str],
        parent: str | None = None
    ) -> CodeItem:
        """
        Process an AST node and extract metadata (name, type, docstring, source, etc.).

        Args:
            node (ast.AST): The AST node to analyze.
            source_lines (List[str]): List of lines from the file source code.
            file_path (Path): Path to the Python file containing the node.
            imports (List[str]): List of import statements found in the file.
            parent (str | None): The parent class name if this node is a method.

        Returns:
            CodeItem: A structured object containing the extracted information.
        """
        start = node.lineno - 1
        end = getattr(node, "end_lineno", start + 1)
        code_text = "\n".join(source_lines[start:end])

        # Determine node type
        if isinstance(node, ast.ClassDef):
            node_type = "class"
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and parent:
            node_type = "method"
        else:
            node_type = "function"

        docstring = ast.get_docstring(node) or ""
        signature = _get_signature_from_node(node)

        return CodeItem(
            name=node.name,
            type=node_type,
            source=code_text,
            docstring=docstring,
            file_path=file_path,
            imports=imports,
            signature=signature,
        )

    def extract_from_file(self, file_path: Path) -> List[CodeItem]:
        """
        Extract CodeItem objects from a single Python file.
        
        This method scans the file for all top-level functions, classes, and methods inside classes, and collects their metadata.
        
        Args:
          file_path (Path): The Python file to analyze.
        Returns:
          List[CodeItem]: A list of extracted CodeItem objects.
        """
        print(f"[INFO] Extracting info from file {file_path} ...")
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        tree = ast.parse(source_code)
        source_lines = source_code.splitlines()

        # Collect import statements
        imports: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""))
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    names = ", ".join(
                        [alias.name + (f" as {alias.asname}" if alias.asname else "") for alias in node.names]
                    )
                    level_dots = "." * node.level
                    imports.append(f"from {level_dots}{module} import {names}")

        items: List[CodeItem] = []

        # --- Extract top-level definitions ---
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                items.append(self._process_node(node, source_lines, file_path, imports))

                # --- If it's a class, extract its methods ---
                if isinstance(node, ast.ClassDef):
                    for sub_node in node.body:
                        if isinstance(sub_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            items.append(
                                self._process_node(sub_node, source_lines, file_path, imports, parent=node.name)
                            )

        print(f"[INFO] Found {len(items)} items in {file_path}")
        return items

def extract_from_path(self) -> List[CodeItem]:
    """
    Extract CodeItem objects from all Python files under the base path (recursively), ignoring virtual environments, caches, and hidden folders.
    
    Returns:
      List[CodeItem]: A list of extracted CodeItem objects from all relevant Python files.
    """
    py_files = [
        f for f in self.base_path.rglob("*.py")
        if "venv" not in f.parts
        and "__pycache__" not in f.parts
        and not any(part.startswith(".") for part in f.parts)
    ]

    all_items: List[CodeItem] = []
    for file_path in py_files:
        all_items.extend(self.extract_from_file(file_path))
    return all_items



def extract_functions_and_classes(path: Union[str, Path]) -> List[CodeItem]:
    """
    Extract functions, methods, and classes from a Python file or directory.
    
    Args:
      path (Union[str, Path]): Path to a Python file or a directory.
    Returns:
      List[CodeItem]: A list of CodeItem objects containing extracted code entities.
    """
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"The path {path} does not exist.")

    extractor = CodeExtractorTool(path.parent if path.is_file() else path)

    if path.is_file() and path.suffix == ".py":
        items = extractor.extract_from_file(path)
    else:
        items = extractor.extract_from_path()

    return items




def get_filtered_code_items(file_path: Path, target_names: Optional[List[str]] = None) -> List[CodeItem]:
    """
    Extract and optionally filter CodeItem objects by name.
    
    Args:
      file_path (Path): Path to the Python file.
      target_names (Optional[List[str]]): List of function/class names to keep.
    Returns:
      List[CodeItem]: Filtered list of CodeItem objects.
    """
    items = extract_functions_and_classes(file_path)
    if target_names:
        items = [i for i in items if i.name in target_names]
    return items


# -----------------------------
# CLI DEBUGGING ENTRY POINT
# Usage:
#   python -m src.utils.code_extractor examples/example.py
# -----------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/utils/code_extractor.py <path_to_python_file_or_directory>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: the path {path} does not exist.")
        sys.exit(1)

    items = extract_functions_and_classes(path)
    print(f"[INFO] Found {len(items)} items in {path}:\n")
    for item in items:
        print(item.__dict__)
        print()