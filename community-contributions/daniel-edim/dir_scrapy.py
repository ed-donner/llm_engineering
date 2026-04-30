import json
import os
import time

TEXT_EXTENSIONS = {
    ".py", ".ipynb", ".md", ".txt"
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCAN_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "repo_tree.json")
DUMP_KWARGS = {"ensure_ascii": False, "indent": 2}


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
    tree = {}

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
            node["encoding"] = "utf-8"
            node["content"] = raw.decode("utf-8")
            files_read += 1
            print(f"  ✓ {rel_path}")
        except UnicodeDecodeError:
            print(f"  ↷ skipped (not utf-8) {rel_path}")
            return None
        except Exception as e:
            print(f"  ✗ {rel_path} ({e})")
            return None
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
            [
                e for e in entries
                if os.path.isfile(os.path.join(current_abs_path, e))
                and os.path.splitext(e.lower())[1] in TEXT_EXTENSIONS
            ],
            key=str.lower,
        )

        current_node = {
            "type":     "dir",
            "name":     os.path.basename(current_abs_path),
            "path":     current_rel_path,
            "local_path": current_abs_path,
            "children": [],
        }

        for f in files:
            file_abs = os.path.join(current_abs_path, f)
            file_rel = f"{current_rel_path}/{f}" if current_rel_path else f
            file_node = read_file(file_abs, file_rel)
            if file_node is None:
                continue
            current_node["children"].append(file_node)

        for d in dirs:
            next_abs = os.path.join(current_abs_path, d)
            next_rel = f"{current_rel_path}/{d}" if current_rel_path else d
            dir_node = build_tree(next_abs, next_rel, depth + 1)
            current_node["children"].append(dir_node)

        return current_node

    print(f"🔍 Scraping local folder: {root_path}\n")

    start = time.time()
    tree = build_tree(root_path)

    elapsed = time.time() - start

    print(f"\n⏱  Done in {elapsed:.1f}s — {files_read} files read")

    if output_file and tree:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(tree, f, **DUMP_KWARGS)
        final_size = os.path.getsize(output_file)
        print(f"💾 Saved → {output_file}  ({final_size / (1024 * 1024):,.2f} MB)")

    return tree
