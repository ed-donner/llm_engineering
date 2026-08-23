from pathlib import Path

import pymupdf4llm


def find_repo_root(start: Path) -> Path:
    """Walk upward to locate the git repository root."""
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise FileNotFoundError("Could not find repository root (.git) from current location")


def convert_pdfs_to_markdown(
    pdf_dir: Path,
    out_dir: Path,
    *,
    header: bool = False,
    footer: bool = False,
) -> int:
    """
    Convert all PDFs in pdf_dir to Markdown files in out_dir.
    Returns the number of PDF files processed.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    for pdf_path in pdf_files:
        md_text = pymupdf4llm.to_markdown(str(pdf_path), header=header, footer=footer)
        md_path = out_dir / f"{pdf_path.stem}.md"
        md_path.write_text(md_text, encoding="utf-8")

    return len(pdf_files)
