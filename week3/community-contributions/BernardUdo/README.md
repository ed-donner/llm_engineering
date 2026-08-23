# Week 3 Contribution: Synthetic Dataset Quality Auditor

This Week 3 submission focuses on evaluating synthetic datasets by comparing a synthetic CSV against a reference CSV and producing a structured markdown report.

## Included Files

- `dataset_quality_auditor.py` - CLI utility for dataset quality checks.
- `week3_quality_auditor.ipynb` - notebook version with manual path override and auto-detection helpers.

## Quality Checks

- Schema overlap (missing/extra columns)
- Missing-value and uniqueness comparison
- Numeric drift (mean/std deltas)
- Categorical drift using Total Variation Distance (TVD)

## Run (CLI)

```bash
python week3/community-contributions/BernardUdo/dataset_quality_auditor.py \
  --reference path/to/reference.csv \
  --synthetic path/to/synthetic.csv \
  --output week3/community-contributions/BernardUdo/quality_report.md
```
