# Screenshot Checklist (PR Artifacts)

Capture these before opening PR.

## Required screenshots

- [ ] `plan` command output (Day 1-5 requirement map)
- [ ] `build` command output showing validation metrics JSON
- [ ] `evaluate` command output with test metrics
- [ ] notebook open with `Python (.venv)` kernel selected
- [ ] Gradio app running at `http://127.0.0.1:7866`
- [ ] one example prediction shown in Gradio UI

## Optional (if fine-tune is run)

- [ ] `prepare-finetune` output showing JSONL paths and counts
- [ ] `start-finetune` output showing `job_id`
- [ ] `status-finetune` output showing recent events

## Suggested naming

- `01-plan.png`
- `02-build-metrics.png`
- `03-evaluate-metrics.png`
- `04-notebook-kernel.png`
- `05-gradio-home.png`
- `06-gradio-prediction.png`
