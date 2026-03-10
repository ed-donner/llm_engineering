from documenter import CodeDocumenter
from pathlib import Path

def load_code(path: Path) -> str:
    return path.read_text()

def main():
    base_dir = Path(__file__).resolve().parent
    code_path = base_dir / "sample_code.py"

    code = code_path.read_text(encoding="utf-8")

    documenter = CodeDocumenter()
    documentation = documenter.document_code(code)

    print("=== DOCUMENTACIÓN GENERADA ===\n")
    print(documentation)

if __name__ == "__main__":
    main()
