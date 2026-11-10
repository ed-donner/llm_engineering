"""Summary of the quality of the generated dataset (displayed as Markdown)."""
from __future__ import annotations

import pandas as pd

from generator import GenStats, meta_column


def summarize(df: pd.DataFrame, spec: dict, stats: GenStats, requested: int) -> str:
    valid_rate = (
        (stats.raw_rows - stats.invalid_rows) / stats.raw_rows * 100 if stats.raw_rows else 0
    )
    lines = [
        "### Ringkasan",
        f"- Requested: **{requested}** rows, generated: **{len(df)}** rows",
        f"- Batches run: {stats.batches} (total failed: {stats.failed_batches})",
        f"- Raw rows from the model: {stats.raw_rows}",
        f"- Validation rate (passing schema): **{valid_rate:.0f}%** "
        f"({stats.invalid_rows} rows discarded)",
        f"- Duplicate / nearly same rows discarded: {stats.duplicate_rows}",
        "",
    ]

    for f in spec["fields"]:
        col = f["name"]
        if col not in df:
            continue
        if f["type"] == "string":
            lens = df[col].astype(str).str.len()
            lines.append(f"- `{col}` (text): average length {lens.mean():.0f} characters "
                         f"(min {lens.min()}, maks {lens.max()}), "
                         f"{df[col].nunique()} unique values")
        elif f["type"] in ("integer", "float"):
            lines.append(f"- `{col}`: min {df[col].min()}, average {df[col].mean():.2f}, "
                         f"max {df[col].max()}")

    lines.append("")
    lines.append("### Distribution")
    cat_cols = [f["name"] for f in spec["fields"] if f["type"] == "category"]
    cat_cols += [meta_column(k) for k in spec["variation_attributes"]]
    for col in cat_cols:
        if col in df:
            counts = df[col].value_counts()
            parts = ", ".join(f"{k} ({v})" for k, v in counts.items())
            lines.append(f"- **{col}**: {parts}")
    return "\n".join(lines)
