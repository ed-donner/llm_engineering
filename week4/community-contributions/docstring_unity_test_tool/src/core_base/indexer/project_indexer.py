from pathlib import Path
import pickle
import hashlib
from typing import List, Dict
from src.core_base.code.code_extractor import CodeExtractorTool, CodeItem


class ProjectIndexer:
    """
    Incremental indexer for a Python project.
    Stores each file's CodeItems separately in `.code_index/indexes/`.
    File hashes are stored in `.code_index/hashes/file_hashes.pkl`.
    Automatically rebuilds only changed files and provides a summary.
    """

    def __init__(self, project_path: Path):
        """
        Initializes the ProjectIndexer with the given project path.
        
        Args:
          project_path (Path): The path to the Python project to index.
        """
        self.project_path = project_path.resolve()

        # Separate folders for eax index
        self.index_dir = self.project_path / ".code_index"
        self.index_dir.mkdir(exist_ok=True)
        self.indexes_dir = self.index_dir / "indexes"
        self.indexes_dir.mkdir(exist_ok=True)
        self.hashes_dir = self.index_dir / "hashes"
        self.hashes_dir.mkdir(exist_ok=True)
        self.hash_file = self.hashes_dir / "file_hashes.pkl"

        self.index: List[CodeItem] = []
        self.file_hashes: Dict[str, str] = {}

        # Load hashes if exist
        if self.hash_file.exists():
            with open(self.hash_file, "rb") as f:
                self.file_hashes = pickle.load(f)

    def _compute_file_hash(self, file_path: Path) -> str:
        """
        Computes the SHA1 hash of the specified file.
        
        Args:
          file_path (Path): The path to the file to be hashed.
        
        Returns:
          str: The SHA1 hash of the file as a hexadecimal string.
        """
        return hashlib.sha1(file_path.read_bytes()).hexdigest()

    def load_or_build(self):
        """
        Loads the index incrementally or rebuilds it by processing changed or new files.
        
        Uses the CodeExtractorTool to extract code items from Python files found in the project path, and updates the index accordingly. It also manages the file hashes to track changes.
        
        Returns:
          None
        """
        extractor = CodeExtractorTool(self.project_path)

        created = 0
        updated = 0
        deleted = 0
        new_file_hashes: Dict[str, str] = {}

        # Solo archivos propios, no carpetas ocultas ni __pycache__
        py_files = [
            f for f in self.project_path.rglob("*.py")
            if not any(part.startswith(".") for part in f.parts)
            and "__pycache__" not in f.parts
        ]

        for py_file in py_files:
            file_hash = self._compute_file_hash(py_file)
            new_file_hashes[str(py_file)] = file_hash
            pickle_path = self.indexes_dir / (py_file.name.replace(".py", ".pkl"))

            if str(py_file) not in self.file_hashes:
                # Nuevo archivo
                code_items = extractor.extract_from_file(py_file)
                with open(pickle_path, "wb") as f:
                    pickle.dump(code_items, f)
                created += len(code_items)

            elif self.file_hashes[str(py_file)] != file_hash:
                # Archivo actualizado
                code_items = extractor.extract_from_file(py_file)
                with open(pickle_path, "wb") as f:
                    pickle.dump(code_items, f)
                updated += len(code_items)

            else:
                # Archivo sin cambios
                if pickle_path.exists():
                    with open(pickle_path, "rb") as f:
                        code_items = pickle.load(f)
                else:
                    # Caso raro: hash existe pero pickle no
                    code_items = extractor.extract_from_file(py_file)
                    with open(pickle_path, "wb") as f:
                        pickle.dump(code_items, f)
                    updated += len(code_items)

            self.index.extend(code_items)

        # Detect deleted files
        deleted_files = set(self.file_hashes.keys()) - set(new_file_hashes.keys())
        for f in deleted_files:
            pkl_path = self.indexes_dir / (Path(f).name.replace(".py", ".pkl"))
            if pkl_path.exists():
                pkl_path.unlink()
            deleted += 1

        # Guardar hashes actualizados
        with open(self.hash_file, "wb") as f:
            pickle.dump(new_file_hashes, f)

        print(f"[ProjectIndexer] Index loaded/built. Total items: {len(self.index)}")
        print(f"[INFO] New items: {created}, Updated items: {updated}, Deleted files: {deleted}")

    # ------------------------
    # Query methods
    # ------------------------
    def query_by_name(self, name: str) -> List[CodeItem]:
        """
        Queries the index for CodeItems matching the given name.
        
        Args:
          name (str): The name of the code item to search for.
        
        Returns:
          List[CodeItem]: A list of CodeItems that match the provided name.
        """
        return [item for item in self.index if item.name == name]

    def query_by_import(self, import_name: str) -> List[CodeItem]:
        """
        Queries the index for CodeItems that import the specified module.
        
        Args:
          import_name (str): The name of the module to search for in imports.
        
        Returns:
          List[CodeItem]: A list of CodeItems that import the specified module.
        """
        return [item for item in self.index if any(import_name in i for i in item.imports)]

    def query_by_file(self, file_path: Path) -> List[CodeItem]:
        """
        Queries the index for CodeItems located in the specified file.
        
        Args:
          file_path (Path): The path to the file to search for CodeItems.
        
        Returns:
          List[CodeItem]: A list of CodeItems that are located in the specified file.
        """
        return [item for item in self.index if item.file_path == file_path.resolve()]

    def all_items(self) -> List[CodeItem]:
        """
        Returns all CodeItems in the current index.
        
        Returns:
          List[CodeItem]: A list of all CodeItems indexed.
        """
        return self.index


# ------------------------
# CLI usage ex $ uv run -m src.core_base.indexer.project_indexer .
# ------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python src/utils/project_indexer.py <project_path>")
        sys.exit(1)

    project_path = Path(sys.argv[1])
    if not project_path.exists():
        print(f"Error: path {project_path} does not exist")
        sys.exit(1)

    indexer = ProjectIndexer(project_path)
    indexer.load_or_build()