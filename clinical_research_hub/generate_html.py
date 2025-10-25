#!/usr/bin/env python3
"""Generate the static site from a saved brief file using the premium template."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from jinja2 import Template


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render the HTML site from a stored clinical brief JSON file."
    )
    parser.add_argument(
        "--brief",
        type=Path,
        help="Path to the brief JSON file. Defaults to the most recent file in the briefs/ directory.",
    )
    parser.add_argument(
        "--brief-date",
        help="Override the brief date displayed on the page. Defaults to the brief JSON's brief_date field if available.",
    )
    parser.add_argument(
        "--templates-dir",
        type=Path,
        default=Path("templates"),
        help="Directory containing the Jinja template (default: templates/).",
    )
    parser.add_argument(
        "--template",
        default="index.html",
        help="Template filename inside the templates directory (default: index.html).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("site/index.html"),
        help="Output HTML path (default: site/index.html).",
    )
    parser.add_argument(
        "--goatcounter-url",
        default="",
        help="Optional GoatCounter analytics URL to inject into the template.",
    )
    return parser.parse_args()


def find_latest_brief(briefs_dir: Path) -> Path:
    json_files = sorted(
        (p for p in briefs_dir.glob("*.json") if p.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not json_files:
        raise FileNotFoundError("No brief JSON files found.")
    return json_files[0]


def load_brief(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def render_template(template_path: Path, context: dict) -> str:
    with template_path.open("r", encoding="utf-8") as handle:
        template = Template(handle.read())
    return template.render(**context)


def main() -> None:
    args = parse_args()

    briefs_dir = Path("briefs")
    if args.brief:
        brief_path = args.brief
    else:
        brief_path = find_latest_brief(briefs_dir)

    brief_data = load_brief(brief_path)

    items = brief_data.get("items", [])
    total_items = brief_data.get("total_items", len(items))

    brief_date = (
        args.brief_date
        or brief_data.get("brief_date")
        or brief_path.stem
        or datetime.utcnow().strftime("%Y-%m-%d")
    )

    template_path = args.templates_dir / args.template
    output_path = args.output

    output_path.parent.mkdir(parents=True, exist_ok=True)

    html_output = render_template(
        template_path,
        {
            "items": items,
            "total_items": total_items,
            "brief_date": brief_date,
            "generated_at": brief_data.get("generated_at", datetime.utcnow().isoformat()),
            "GOATCOUNTER_URL": args.goatcounter_url,
        },
    )

    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(html_output)

    print(f"✅ Generated HTML with {len(items)} articles")
    print(f"📁 Output: {output_path}")
    print(f"🗂  Source brief: {brief_path}")


if __name__ == "__main__":
    main()
