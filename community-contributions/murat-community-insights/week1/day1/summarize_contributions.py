"""
Summarize all GitHub community contribution folders and save results to JSON.

This script:
1. Scans the main community-contributions directory
2. Extracts readable text from each contribution folder
3. Sends the content to an LLM for summarization
4. Saves all summaries to results/community_contribution_summaries.json
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# --------------------------------------------------
# Load environment variables from repo root
# --------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(REPO_ROOT / ".env")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Check your .env file.")

client = OpenAI(api_key=api_key)

# --------------------------------------------------
# Paths
# --------------------------------------------------
CURRENT_DIR = Path(__file__).parent
RESULTS_DIR = CURRENT_DIR / "results"
OUTPUT_FILE = RESULTS_DIR / "community_contribution_summaries.json"

# Main source folder to analyze
BASE_DIR = REPO_ROOT / "community-contributions"

# Skip your own folder so you do not summarize yourself
EXCLUDED_DIR_NAMES = {"murat-community-insights"}

# --------------------------------------------------
# Prompt
# --------------------------------------------------
SYSTEM_PROMPT = """
You are an assistant that summarizes GitHub community contribution projects.

Your task:
- summarize each contribution accurately
- identify the likely purpose of the project
- identify likely category
- list main technologies only if clearly visible
- do not invent details
- if evidence is weak, say 'insufficient evidence'

Return in this format:
Title:
Summary:
Category:
Technologies:
Confidence:
"""

# --------------------------------------------------
# Extract useful text from each project folder
# --------------------------------------------------
def extract_project_text(project_dir: Path) -> str:
    priority_files = [
        "README.md",
        "readme.md",
        "README.MD",
        "project.md",
        "description.txt",
    ]

    collected_parts = []

    # First try standard descriptive files
    for fname in priority_files:
        fpath = project_dir / fname
        if fpath.exists() and fpath.is_file():
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore")
                if text.strip():
                    collected_parts.append(f"\n--- {fname} ---\n{text[:12000]}")
            except Exception:
                pass

    if collected_parts:
        return "\n".join(collected_parts)

    # Fallback to a few readable files
    fallback_exts = {".py", ".ipynb", ".js", ".ts", ".md", ".txt"}

    for fpath in sorted(project_dir.rglob("*")):
        if fpath.is_file() and fpath.suffix.lower() in fallback_exts:
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore")
                if text.strip():
                    collected_parts.append(f"\n--- {fpath.name} ---\n{text[:4000]}")
            except Exception:
                pass

        if len(collected_parts) >= 3:
            break

    return "\n".join(collected_parts) if collected_parts else "No readable content found."

# --------------------------------------------------
# Summarize one project
# --------------------------------------------------
def summarize_project(project_name: str, project_text: str) -> str:
    user_prompt = f"""
Analyze this contribution folder.

Folder name:
{project_name}

Project content:
{project_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content

# --------------------------------------------------
# Main pipeline
# --------------------------------------------------
def main():
    if not BASE_DIR.exists():
        raise FileNotFoundError(f"Base directory not found: {BASE_DIR}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    for project_dir in sorted(BASE_DIR.iterdir()):
        if not project_dir.is_dir():
            continue

        if project_dir.name in EXCLUDED_DIR_NAMES:
            continue

        print(f"Processing: {project_dir.name}")

        project_text = extract_project_text(project_dir)
        summary = summarize_project(project_dir.name, project_text)

        results.append({
            "project_name": project_dir.name,
            "summary": summary,
        })

        print(f"Done: {project_dir.name}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Saved summaries to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()