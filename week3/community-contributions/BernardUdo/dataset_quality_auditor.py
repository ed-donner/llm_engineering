"""
Dataset Quality Auditor for Week 3 synthetic data projects.

Compares a synthetic CSV against a reference CSV and writes a markdown report
with simple, practical quality checks.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def _safe_div(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return a / b


def _format_float(value: float) -> str:
    return f"{value:.4f}"


def _display_col(col: object) -> str:
    text = str(col)
    # Keep markdown tables stable even for unusual column names.
    text = text.replace("`", "\\`").replace("|", "\\|").replace("\n", " ")
    return text


def _distribution_distance(ref: pd.Series, syn: pd.Series) -> float:
    ref_dist = ref.value_counts(normalize=True, dropna=False)
    syn_dist = syn.value_counts(normalize=True, dropna=False)
    categories = ref_dist.index.union(syn_dist.index)
    ref_aligned = ref_dist.reindex(categories, fill_value=0.0)
    syn_aligned = syn_dist.reindex(categories, fill_value=0.0)
    return float(0.5 * (ref_aligned - syn_aligned).abs().sum())


def _numeric_metrics(ref: pd.Series, syn: pd.Series) -> dict[str, float]:
    ref_clean = ref.dropna()
    syn_clean = syn.dropna()
    ref_mean = float(ref_clean.mean()) if not ref_clean.empty else 0.0
    syn_mean = float(syn_clean.mean()) if not syn_clean.empty else 0.0
    ref_std = float(ref_clean.std(ddof=0)) if len(ref_clean) > 1 else 0.0
    syn_std = float(syn_clean.std(ddof=0)) if len(syn_clean) > 1 else 0.0
    mean_delta = abs(syn_mean - ref_mean)
    std_delta = abs(syn_std - ref_std)
    return {
        "ref_mean": ref_mean,
        "syn_mean": syn_mean,
        "mean_delta": mean_delta,
        "ref_std": ref_std,
        "syn_std": syn_std,
        "std_delta": std_delta,
    }


def _load_csv_pair(reference_path: Path, synthetic_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    # First try default header parsing.
    ref_default = pd.read_csv(reference_path)
    syn_default = pd.read_csv(synthetic_path)

    ref_cols = [str(c) for c in ref_default.columns]
    syn_cols = [str(c) for c in syn_default.columns]
    shared_cols = len(set(ref_cols).intersection(set(syn_cols)))

    def _looks_like_bad_header(col: str) -> bool:
        col_stripped = col.strip()
        return (
            "\n" in col_stripped
            or len(col_stripped) > 80
            or col_stripped.isdigit()
            or ":" in col_stripped
        )

    suspicious_header_count = sum(_looks_like_bad_header(c) for c in ref_cols + syn_cols)

    # Fallback to headerless if overlap is weak and header tokens look suspicious.
    if shared_cols == 0 or (shared_cols <= 1 and suspicious_header_count >= 2):
        ref_df = pd.read_csv(reference_path, header=None)
        syn_df = pd.read_csv(synthetic_path, header=None)

        max_cols = max(ref_df.shape[1], syn_df.shape[1])
        column_names = [f"col_{i}" for i in range(max_cols)]
        ref_df.columns = column_names[: ref_df.shape[1]]
        syn_df.columns = column_names[: syn_df.shape[1]]
        return ref_df, syn_df, "Loaded as headerless CSVs (assigned col_0, col_1, ...)."

    ref_default.columns = [str(c) for c in ref_default.columns]
    syn_default.columns = [str(c) for c in syn_default.columns]
    return ref_default, syn_default, "Loaded with CSV headers."


def build_report(reference_path: Path, synthetic_path: Path) -> str:
    ref_df, syn_df, load_mode = _load_csv_pair(reference_path, synthetic_path)

    ref_cols = set(ref_df.columns)
    syn_cols = set(syn_df.columns)
    common_cols = sorted(ref_cols.intersection(syn_cols))
    missing_in_synthetic = sorted(ref_cols - syn_cols)
    extra_in_synthetic = sorted(syn_cols - ref_cols)

    report: list[str] = []
    report.append("# Synthetic Dataset Quality Report")
    report.append("")
    report.append("## File Overview")
    report.append(f"- Parsing mode: `{load_mode}`")
    report.append(f"- Reference rows: `{len(ref_df)}`")
    report.append(f"- Synthetic rows: `{len(syn_df)}`")
    report.append(f"- Reference columns: `{len(ref_cols)}`")
    report.append(f"- Synthetic columns: `{len(syn_cols)}`")
    report.append(f"- Common columns: `{len(common_cols)}`")
    report.append("")

    report.append("## Schema Alignment")
    report.append(
        f"- Column overlap score: `{_format_float(_safe_div(len(common_cols), max(len(ref_cols), 1)))}`"
    )
    report.append(f"- Missing in synthetic: `{missing_in_synthetic or 'None'}`")
    report.append(f"- Extra in synthetic: `{extra_in_synthetic or 'None'}`")
    report.append("")

    report.append("## Missingness & Uniqueness")
    report.append("| Column | Ref missing % | Syn missing % | Ref unique % | Syn unique % |")
    report.append("|---|---:|---:|---:|---:|")
    for col in common_cols:
        ref_missing = _safe_div(ref_df[col].isna().sum(), len(ref_df)) * 100
        syn_missing = _safe_div(syn_df[col].isna().sum(), len(syn_df)) * 100
        ref_unique = _safe_div(ref_df[col].nunique(dropna=False), len(ref_df)) * 100
        syn_unique = _safe_div(syn_df[col].nunique(dropna=False), len(syn_df)) * 100
        col_label = _display_col(col)
        report.append(
            f"| `{col_label}` | {_format_float(ref_missing)} | {_format_float(syn_missing)} | "
            f"{_format_float(ref_unique)} | {_format_float(syn_unique)} |"
        )
    report.append("")

    numeric_cols = [
        c
        for c in common_cols
        if pd.api.types.is_numeric_dtype(ref_df[c]) and pd.api.types.is_numeric_dtype(syn_df[c])
    ]
    if numeric_cols:
        report.append("## Numeric Column Drift")
        report.append("| Column | Ref mean | Syn mean | |delta mean| | Ref std | Syn std | |delta std| |")
        report.append("|---|---:|---:|---:|---:|---:|---:|")
        for col in numeric_cols:
            metrics = _numeric_metrics(ref_df[col], syn_df[col])
            col_label = _display_col(col)
            report.append(
                f"| `{col_label}` | {_format_float(metrics['ref_mean'])} | {_format_float(metrics['syn_mean'])} | "
                f"{_format_float(metrics['mean_delta'])} | {_format_float(metrics['ref_std'])} | "
                f"{_format_float(metrics['syn_std'])} | {_format_float(metrics['std_delta'])} |"
            )
        report.append("")

    categorical_cols = [c for c in common_cols if c not in numeric_cols]
    if categorical_cols:
        report.append("## Categorical Distribution Distance (TVD)")
        report.append("| Column | TVD distance |")
        report.append("|---|---:|")
        for col in categorical_cols:
            tvd = _distribution_distance(ref_df[col], syn_df[col])
            col_label = _display_col(col)
            report.append(f"| `{col_label}` | {_format_float(float(tvd))} |")
        report.append("")

    report.append("## Quick Interpretation")
    report.append("- Lower drift and lower TVD generally indicate better alignment.")
    report.append("- Some drift is normal when synthetic row count differs from reference.")
    report.append("- Use this report as a first-pass quality check, not a privacy guarantee.")
    report.append("")

    return "\n".join(report)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit synthetic dataset quality.")
    parser.add_argument("--reference", type=Path, required=True, help="Path to reference CSV.")
    parser.add_argument("--synthetic", type=Path, required=True, help="Path to synthetic CSV.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("quality_report.md"),
        help="Path for markdown report output.",
    )
    return parser.parse_args()


def _validate_inputs(reference: Path, synthetic: Path) -> None:
    if not reference.exists():
        raise FileNotFoundError(f"Reference CSV not found: {reference}")
    if not synthetic.exists():
        raise FileNotFoundError(f"Synthetic CSV not found: {synthetic}")


def main() -> None:
    args = parse_args()
    _validate_inputs(args.reference, args.synthetic)
    report = build_report(args.reference, args.synthetic)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Quality report written to: {args.output}")


if __name__ == "__main__":
    main()
