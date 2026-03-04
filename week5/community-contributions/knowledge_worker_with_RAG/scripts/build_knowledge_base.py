"""
Build the knowledge base for RAG: fetch only LiteLLM documentation (how to use LiteLLM)
from GitHub (clone or API) into knowledge-base/, preserving directory structure.
No tests or other repo content—only docs for the RAG chatbot.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import urllib.request

REPO = "BerriAI/litellm"
# Only LiteLLM docs (for RAG); no tests or other repo content.
DOCS_SOURCE = "docs/my-website/docs"
BRANCH = "main"
GITHUB_RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
GITHUB_API = f"https://api.github.com/repos/{REPO}/contents"


def find_project_root() -> Path:
    """Project root: directory containing knowledge-base/ and scripts/."""
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "knowledge-base").is_dir() and (p / "scripts").is_dir():
            return p
        p = p.parent
    return Path(__file__).resolve().parent.parent


def fetch_via_clone(project_root: Path, knowledge_base: Path) -> int:
    """Clone repo and copy only docs (LiteLLM documentation for RAG). Returns file count or -1."""
    tmp = project_root / ".tmp_litellm_clone"
    if tmp.exists():
        try:
            shutil.rmtree(tmp)
        except OSError:
            # Windows may lock .git files; use a unique dir for this run.
            tmp = project_root / f".tmp_litellm_clone_{os.getpid()}"
    try:
        tmp.mkdir(parents=True, exist_ok=True)
        print("Cloning LiteLLM repo (shallow, docs only)...")
        # Clone with --no-checkout to avoid Windows "filename too long" on checkout.
        r = subprocess.run(
            [
                "git", "clone", "--depth", "1", "--branch", BRANCH,
                "--no-checkout",
                f"https://github.com/{REPO}.git", str(tmp),
            ],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            print(r.stderr or r.stdout, file=sys.stderr)
            return -1
        # Checkout only docs folder (sparse checkout) so long paths in tests/ are never created.
        for cmd in [
            ["git", "sparse-checkout", "init", "--cone"],
            ["git", "sparse-checkout", "set", DOCS_SOURCE],
            ["git", "checkout"],
        ]:
            r = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)
            if r.returncode != 0:
                print(r.stderr or r.stdout, file=sys.stderr)
                return -1
        src = tmp / DOCS_SOURCE
        if not src.is_dir():
            return -1
        count = 0
        for ext in ("*.md", "*.mdx"):
            for f in src.rglob(ext):
                rel = f.relative_to(src)
                dest = knowledge_base / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)
                count += 1
        return count
    finally:
        if tmp.exists():
            try:
                shutil.rmtree(tmp)
            except OSError:
                pass  # Windows may lock .git files; leave dir for manual cleanup


def fetch_via_api(project_root: Path, knowledge_base: Path) -> int:
    """Fetch docs via GitHub API (recursive tree + raw content). No git required."""
    import json

    def get_tree(path: str):
        url = f"{GITHUB_API}/{path}?ref={BRANCH}"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())

    def collect_files(entries, prefix: str) -> list[tuple[str, str]]:
        out = []
        for e in entries:
            name = e["name"]
            path = f"{prefix}/{name}" if prefix else name
            if e.get("type") == "dir":
                sub = get_tree(path)
                out.extend(collect_files(sub, path))
            elif name.endswith(".md") or name.endswith(".mdx"):
                out.append((path, e.get("download_url")))
        return out

    print("Fetching doc tree via GitHub API...")
    try:
        root_entries = get_tree(DOCS_SOURCE)
    except Exception as e:
        print(f"API tree failed: {e}", file=sys.stderr)
        return -1
    files = collect_files(root_entries, DOCS_SOURCE)
    count = 0
    for rel_path, url in files:
        if not url:
            continue
        rel = Path(rel_path).relative_to(DOCS_SOURCE)
        dest = knowledge_base / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                dest.write_bytes(r.read())
            count += 1
        except Exception as e:
            print(f"Skip {rel}: {e}", file=sys.stderr)
    return count


def main() -> int:
    project_root = find_project_root()
    knowledge_base = project_root / "knowledge-base"
    knowledge_base.mkdir(parents=True, exist_ok=True)
    # Prefer git clone (fast); fall back to API when git is not available
    count = fetch_via_clone(project_root, knowledge_base)
    if count < 0:
        print("Git clone failed or git not installed, trying GitHub API...")
        count = fetch_via_api(project_root, knowledge_base)
    if count < 0:
        print("Failed to build knowledge base.", file=sys.stderr)
        return 1
    print(f"Copied {count} files to {knowledge_base}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
