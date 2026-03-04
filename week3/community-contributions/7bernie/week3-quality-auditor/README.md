# Week 3 Contribution: Synthetic Dataset Quality Auditor

This contribution adds a lightweight quality-auditing utility for Week 3 synthetic data projects.

Most Week 3 submissions focus on generation. This tool focuses on **evaluation** by comparing a synthetic CSV against a reference CSV and producing a markdown quality report.

## What It Checks

- Schema overlap (missing/extra columns)
- Missing-value rate differences
- Uniqueness rate differences
- Numeric drift (mean/std deltas)
- Categorical drift with Total Variation Distance (TVD)

## Files

- `dataset_quality_auditor.py` - command-line utility that generates report output.

## Install

From the repo root:

```bash
pip install pandas
```

## Run

```bash
python week3/community-contributions/7bernie/week3-quality-auditor/dataset_quality_auditor.py \
  --reference path/to/reference.csv \
  --synthetic path/to/synthetic.csv \
  --output week3/community-contributions/7bernie/week3-quality-auditor/quality_report.md
```

## Why This Helps Week 3

Week 3 teaches how to generate useful synthetic datasets. This contribution gives you a practical way to quickly evaluate whether generated data still resembles the intended reference data.
