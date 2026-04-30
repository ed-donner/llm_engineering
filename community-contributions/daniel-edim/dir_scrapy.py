import base64
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

TEXT_EXTENSIONS = {
    ".py", ".ipynb", ".md", ".txt", ".rst", ".csv", ".tsv",
    ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".env",
    ".html", ".htm", ".css", ".js", ".ts", ".jsx", ".tsx",
    ".sh", ".bash", ".zsh", ".bat", ".ps1", ".sql",
    ".r", ".R", ".jl", ".go", ".java", ".c", ".cpp",
    ".h", ".hpp", ".cs", ".rb", ".php", ".xml", ".svg",
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCAN_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "repo_tree.json")


def scrape_local(
    root_path: str = DEFAULT_SCAN_ROOT,
    output_file: str = DEFAULT_OUTPUT_FILE,
) -> dict:
    """
    Scrape a local folder into a nested JSON tree.

    Parameters
    ----------
    root_path   : Local folder path. Defaults to the parent
                  `community-contributions` directory.
    output_file : Where to save the result. Pass None to skip saving.

    Returns
    -------
    dict — the (possibly partial) nested tree
    """

    root_path = os.path.abspath(root_path)
    if not os.path.isdir(root_path):
        raise ValueError(f"Cannot find local folder: {root_path}")

    files_read = 0

    # ── Read a single file's content ──────────────────────────────────────────
    def read_file(file_path, rel_path):
        nonlocal files_read
        file_name = os.path.basename(file_path)
        node = {
            "type": "file",
            "name": file_name,
            "path": rel_path,
            "size": os.path.getsize(file_path),
        }
        try:
            with open(file_path, "rb") as f:
                raw = f.read()
            ext = os.path.splitext(file_name.lower())[1]
            if ext in TEXT_EXTENSIONS:
                try:
                    node["encoding"] = "utf-8"
                    node["content"]  = raw.decode("utf-8")
                except UnicodeDecodeError:
                    node["encoding"] = "base64"
                    node["content"]  = base64.b64encode(raw).decode()
            else:
                node["encoding"] = "base64"
                node["content"]  = base64.b64encode(raw).decode()
            files_read += 1
            print(f"  ✓ {rel_path}")
        except Exception as e:
            node["encoding"] = "error"
            node["content"]  = str(e)
            print(f"  ✗ {rel_path} ({e})")
        return node

    # ── Recursively build the tree ────────────────────────────────────────────
    def build_tree(current_abs_path, current_rel_path="", depth=0):
        print("  " * depth + f"📂 {current_rel_path or '(root)'}")
        entries = os.listdir(current_abs_path)
        dirs = sorted(
            [e for e in entries if os.path.isdir(os.path.join(current_abs_path, e))],
            key=str.lower,
        )
        files = sorted(
            [e for e in entries if os.path.isfile(os.path.join(current_abs_path, e))],
            key=str.lower,
        )

        with ThreadPoolExecutor(max_workers=5) as ex:
            futures = {}
            for f in files:
                file_abs = os.path.join(current_abs_path, f)
                file_rel = f"{current_rel_path}/{f}" if current_rel_path else f
                futures[ex.submit(read_file, file_abs, file_rel)] = f
            file_nodes = []
            for ft in as_completed(futures):
                file_nodes.append(ft.result())
            file_nodes.sort(key=lambda n: n["name"].lower())

        dir_nodes = []
        for d in dirs:
            next_abs = os.path.join(current_abs_path, d)
            next_rel = f"{current_rel_path}/{d}" if current_rel_path else d
            dir_nodes.append(build_tree(next_abs, next_rel, depth + 1))

        return {
            "type":     "dir",
            "name":     os.path.basename(current_abs_path),
            "path":     current_rel_path,
            "local_path": current_abs_path,
            "children": dir_nodes + file_nodes,
        }

    print(f"🔍 Scraping local folder: {root_path}\n")

    start = time.time()
    tree = {}

    tree = build_tree(root_path)

    elapsed = time.time() - start

    print(f"\n⏱  Done in {elapsed:.1f}s — {files_read} files read")

    if output_file and tree:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved → {output_file}  ({os.path.getsize(output_file) / 1024:,.1f} KB)")

    return tree
