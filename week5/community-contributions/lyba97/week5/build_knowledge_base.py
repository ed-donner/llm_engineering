"""
build_knowledge_base.py

Fetches the WCAG 2.2 machine-readable JSON from the W3C quickref repo and
writes one Markdown file per success criterion into:

    knowledge-base/success-criteria/

Run once before using the notebook:

    pip install httpx
    python build_knowledge_base.py

No API key required. Output: 86 .md files (one per SC in WCAG 2.2).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SOURCES = [
    "https://www.w3.org/WAI/WCAG22/wcag.json",
    "https://raw.githubusercontent.com/w3c/wai-wcag-quickref/gh-pages/_data/wcag22.json",
]

OUT_DIR = Path(__file__).parent / "knowledge-base" / "a11y" / "success-criteria"


# ---------------------------------------------------------------------------
# Step 1: fetch
# ---------------------------------------------------------------------------

def fetch_wcag_json() -> dict:
    try:
        import httpx
    except ImportError:
        sys.exit("Please install httpx first:  pip install httpx")

    for url in SOURCES:
        try:
            resp = httpx.get(url, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json()
            print(f"Fetched WCAG JSON from {url}")
            return data
        except Exception as exc:
            print(f"  ! {url} failed: {exc}", file=sys.stderr)

    sys.exit("All sources failed — check your network connection.")


# ---------------------------------------------------------------------------
# Step 2: normalise — flatten tree into one record per SC
# ---------------------------------------------------------------------------

def _details_to_text(details: list[dict]) -> str:
    parts: list[str] = []
    for block in details or []:
        btype = block.get("type")
        if btype == "ulist":
            for item in block.get("items", []):
                handle = item.get("handle", "")
                text = item.get("text", "")
                parts.append(f"- {handle}: {text}" if handle else f"- {text}")
        elif btype == "note":
            parts.append(f"Note: {block.get('text', '')}")
        elif "text" in block:
            parts.append(block["text"])
    return "\n".join(p for p in parts if p.strip())


def _technique_ids(techniques: dict) -> dict[str, list[str]]:
    def walk(node) -> list[str]:
        ids: list[str] = []
        if isinstance(node, dict):
            if "id" in node and "technology" in node:
                ids.append(node["id"])
            for v in node.values():
                ids.extend(walk(v))
        elif isinstance(node, list):
            for item in node:
                ids.extend(walk(item))
        return ids

    return {
        cat: sorted(set(walk(techniques.get(cat, []))))
        for cat in ("sufficient", "advisory", "failure")
    }


def normalise(data: dict) -> list[dict]:
    records = []
    for principle in data["principles"]:
        for guideline in principle["guidelines"]:
            for sc in guideline["successcriteria"]:
                versions = sc.get("versions", [])
                if versions and "2.2" not in versions:
                    continue  # skip removed SCs (e.g. 4.1.1 Parsing)

                tech = _technique_ids(sc.get("techniques", {}))
                detail_text = _details_to_text(sc.get("details", []))

                embed_text = (
                    f"WCAG {sc['num']} {sc['handle']} (Level {sc['level']})\n"
                    f"Principle: {principle['handle']}. "
                    f"Guideline {guideline['num']}: {guideline['handle']}.\n\n"
                    f"{sc['title']}"
                )
                if detail_text:
                    embed_text += f"\n\n{detail_text}"

                records.append({
                    "id": sc["num"],
                    "slug": sc["id"],
                    "level": sc["level"],
                    "principle": principle["handle"],
                    "guideline": f"{guideline['num']} {guideline['handle']}",
                    "title": sc["handle"],
                    "text": embed_text,
                    "related_failures": tech["failure"],
                    "url": (
                        f"https://www.w3.org/WAI/WCAG22/Understanding/{sc['id']}.html"
                    ),
                })
    return records


# ---------------------------------------------------------------------------
# Step 3: write one markdown file per SC
# ---------------------------------------------------------------------------

def write_markdown_files(records: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for r in records:
        filename = OUT_DIR / f"{r['id']} {r['slug']}.md"
        failures = (
            ", ".join(r["related_failures"]) if r["related_failures"] else "none mapped"
        )
        content = f"""# WCAG {r['id']} — {r['title']}

- **Level:** {r['level']}
- **Principle:** {r['principle']}
- **Guideline:** {r['guideline']}
- **Understanding:** {r['url']}

## Requirement
{r['text']}

## Related failure techniques
{failures}
"""
        filename.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Building WCAG 2.2 knowledge base...")

    data = fetch_wcag_json()
    records = normalise(data)
    write_markdown_files(records)

    levels = {lvl: sum(1 for r in records if r["level"] == lvl)
              for lvl in ("A", "AA", "AAA")}

    print(f"\nDone. Wrote {len(records)} files to {OUT_DIR}/")
    print(f"  Level A: {levels['A']}  |  AA: {levels['AA']}  |  AAA: {levels['AAA']}")
    print(f"\nNext: open the notebook and run all cells.")


if __name__ == "__main__":
    main()
