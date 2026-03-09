"""
Gradio UI to run RAG evaluation: MRR (retrieval) and LLM-as-judge (answer quality).
Run from week5/IbrahimSheriff: python eval_app.py
"""
from __future__ import annotations

import json
from pathlib import Path

import gradio as gr

from evaluation import (
    EvalExample,
    default_eval_set,
    compute_mrr,
    run_answer_eval,
    load_eval_set_from_json,
)


def _format_doc_source(doc) -> str:
    raw = (doc.metadata or {}).get("source", "")
    return Path(raw).name if raw else "(no source)"


def run_evaluation(use_default: bool, custom_json: str, progress: gr.Progress | None = None):
    """
    Run full eval: MRR then LLM judge on each answer.
    Yields (summary, details) so the UI updates during the run instead of staying stagnant.
    """
    def update_progress(frac: float, msg: str) -> None:
        if progress is not None:
            progress(frac, desc=msg)

    # Update UI immediately so it doesn't look stagnant
    yield "⏳ **Starting evaluation...**", ""

    # Parse eval set
    if use_default:
        eval_set = default_eval_set()
    else:
        if not (custom_json or custom_json.strip()):
            yield "⚠️ Provide a JSON eval set (list of {question, expected_sources?, expected_answer?}).", ""
            return
        try:
            data = json.loads(custom_json)
            eval_set = [
                EvalExample(
                    question=item["question"],
                    expected_sources=item.get("expected_sources", []),
                    expected_answer=item.get("expected_answer"),
                )
                for item in data
            ]
        except json.JSONDecodeError as e:
            yield f"⚠️ Invalid JSON: {e}", ""
            return
        except (KeyError, TypeError) as e:
            yield f"⚠️ Each item must have 'question'; optional 'expected_sources', 'expected_answer': {e}", ""
            return

    if not eval_set:
        yield "⚠️ Eval set is empty.", ""
        return

    try:
        update_progress(0.0, "Running retrieval (MRR)...")
        yield "⏳ **Running retrieval (MRR)...** This may take a minute.", ""

        mean_mrr, mrr_results = compute_mrr(eval_set)
        mrr_detail_lines = []
        for ex, docs, mrr in mrr_results:
            sources = ", ".join(_format_doc_source(d) for d in docs[:5])
            mrr_detail_lines.append(f"- **Q:** {ex.question[:60]}… → MRR = {mrr:.3f} | Top sources: {sources}")

        update_progress(0.4, "Running RAG answers + LLM judge...")
        yield "⏳ **MRR done.** Running RAG answers and LLM judge (this is slow)...", ""

        mean_score, answer_results = run_answer_eval(eval_set)
        detail_lines = []
        for i, (ex, answer, docs, judge) in enumerate(answer_results, 1):
            sources = ", ".join(_format_doc_source(d) for d in docs[:5])
            detail_lines.append(
                f"### Example {i}: {ex.question}\n"
                f"- **Retrieved sources:** {sources}\n"
                f"- **Model answer:** {answer[:400]}{'…' if len(answer) > 400 else ''}\n"
                f"- **Judge score:** {judge.score}/5 — {judge.reasoning}\n"
            )

        summary = (
            f"## Evaluation results\n\n"
            f"- **MRR (retrieval):** {mean_mrr:.4f}\n\n"
            f"- **Mean LLM judge score (1–5):** {mean_score:.2f}\n\n"
            f"### MRR per query\n" + "\n".join(mrr_detail_lines)
        )
        details = "## Per-example details (answer + judge)\n\n" + "\n\n".join(detail_lines)
        update_progress(1.0, "Done")
        yield summary, details
    except Exception as e:
        import traceback
        yield f"❌ **Error:** {e}\n\n```\n{traceback.format_exc()}\n```", ""


def main():
    base = Path(__file__).parent
    default_json = ""
    eval_data_path = base / "eval_data.json"
    if eval_data_path.exists():
        default_json = eval_data_path.read_text(encoding="utf-8")

    with gr.Blocks(title="RAG Evaluation") as demo:
        gr.Markdown("# RAG Evaluation — MRR & LLM-as-judge\nRun retrieval + answer evals and see MRR and per-response judge scores.")
        use_default = gr.Radio(
            choices=["default", "custom"],
            value="default",
            label="Eval set",
            info="Use default Galdunx eval set or paste custom JSON.",
        )
        custom_json = gr.Textbox(
            label="Custom eval set (JSON)",
            placeholder='[{"question": "...", "expected_sources": ["file.md"], "expected_answer": "..."}, ...]',
            value=default_json,
            lines=12,
        )
        run_btn = gr.Button("Run evaluation", variant="primary")
        summary = gr.Markdown(label="Summary")
        details = gr.Markdown(label="Details")

        def run(choice: str, json_text: str):
            """Generator: yield progress updates so the UI is not stagnant."""
            yield from run_evaluation(choice == "default", json_text, progress=None)

        run_btn.click(
            fn=run,
            inputs=[use_default, custom_json],
            outputs=[summary, details],
            show_progress=True,
        )

    demo.launch(inbrowser=True)


if __name__ == "__main__":
    main()
