"""Gradio UI: run a multi-LLM arena and show judge scores."""

import html
import os
import signal
import gradio as gr

from markdown_it import MarkdownIt
from dotenv import load_dotenv
from src.arena import run_arena_streaming
from src.config import AVAILABLE_MODELS, DEFAULT_MODELS, JUDGE_MODEL
from src.db import clear_history, get_history, init_db, save_session
from src.judge import evaluate_responses

load_dotenv()
init_db()

_md = MarkdownIt("commonmark", {"html": False, "breaks": True})

MODEL_LABEL = {m["id"]: m["label"] for m in AVAILABLE_MODELS}
MODEL_CHOICES = [(m["label"], m["id"]) for m in AVAILABLE_MODELS]

DEFAULT_SYSTEM_PROMPT = "You are a helpful, concise assistant."
DEFAULT_PROMPT = "Explain async/await in Python in one paragraph."

SPINNER = (
    '<div style="display:flex;align-items:center;gap:8px;padding:12px 0;">'
    '<div class="arena-spinner"></div>'
    '<span style="opacity:0.6;font-size:0.9em;">Generating...</span></div>'
)

JUDGE_SPINNER = (
    '<div style="display:flex;align-items:center;gap:8px;padding:16px;">'
    '<div class="arena-spinner"></div>'
    '<span style="opacity:0.6;">Judge is evaluating responses...</span></div>'
)

CSS = """
@keyframes arena-spin {to{transform:rotate(360deg)}}

.arena-spinner {
    width: 18px; height: 18px;
    border: 3px solid rgba(255,255,255,0.15);
    border-top-color: #6366f1;
    border-radius: 50%;
    animation: arena-spin .8s linear infinite;
}

.arena-card {
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    background: rgba(255,255,255,0.02);
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.arena-card.winner {
    border-color: #6366f1;
    box-shadow: 0 0 20px rgba(99,102,241,0.15);
}

.arena-card h3 { margin: 0 0 12px 0; }
.arena-card .content pre {
    background: rgba(255,255,255,0.05);
    border-radius: 8px;
    padding: 12px;
    overflow-x: auto;
}

.arena-card .content code {
    background: rgba(255,255,255,0.06);
    padding: 1px 4px;
    border-radius: 4px;
    font-size: 0.9em;
}

.arena-card .content pre code {
    background: none;
    padding: 0;
}

.arena-badge {
    display: inline-block;
    background: #6366f1;
    color: white;
    font-size: 0.75em;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 999px;
    margin-left: 8px;
    vertical-align: middle;
}

.arena-tokens {
    opacity: 0.5;
    font-size: 0.85em;
    margin-left: 6px;
}

.eval-panel {
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 12px;
    padding: 24px;
    margin-top: 8px;
    background: rgba(99,102,241,0.04);
}

.eval-panel h2 { margin: 0 0 16px 0; color: #6366f1; }
.score-bar-track {
    background: rgba(255,255,255,0.06);
    border-radius: 6px;
    height: 8px;
    width: 100%;
    margin: 4px 0 8px 0;
}

.score-bar-fill {
    height: 100%;
    border-radius: 6px;
    background: linear-gradient(90deg, #6366f1, #818cf8);
    transition: width 0.4s ease;
}

.hist-card {
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 12px;
    background: rgba(255,255,255,0.02);
}

.hist-card:hover { border-color: rgba(99,102,241,0.3); }
.hist-meta {
    display: flex; gap: 16px; flex-wrap: wrap;
    margin-top: 8px; font-size: 0.85em; opacity: 0.6;
}

.hist-prompt { margin: 0; font-size: 0.95em; }
.hist-winner {
    display: inline-block;
    background: rgba(99,102,241,0.15);
    color: #818cf8;
    font-size: 0.78em; font-weight: 600;
    padding: 2px 10px; border-radius: 999px; margin-left: 8px;
}

.hist-chip {
    display: inline-block;
    font-size: 0.78em;
    padding: 2px 8px; border-radius: 6px; margin-right: 6px;
}
"""


def _esc(text: str) -> str:
    """HTML-escape user/LLM content to prevent XSS."""
    return html.escape(text, quote=True)


def _render_md(text: str) -> str:
    """Render markdown to safe HTML (no raw HTML passthrough)."""
    return _md.render(text)


def _format_responses(
    completed: dict[str, dict],
    pending: list[str],
    winner_id: str = "",
) -> str:
    """Build HTML for model response cards with optional spinners."""
    out = ""

    for model_id, r in completed.items():
        label = _esc(MODEL_LABEL.get(r["model"], r["model"]))
        is_winner = r["model"] == winner_id
        cls = "arena-card winner" if is_winner else "arena-card"
        badge = '<span class="arena-badge">WINNER</span>' if is_winner else ""

        meta_parts = []

        if r.get("elapsed_s") is not None:
            meta_parts.append(f"{r['elapsed_s']}s")

        if r.get("tokens"):
            meta_parts.append(f"{r['tokens']} tokens")

        meta = (
            f'<span class="arena-tokens">{" · ".join(meta_parts)}</span>'
            if meta_parts else ""
        )

        if r["error"]:
            body = f'<em style="color:#ef4444;">Error: {_esc(r["error"])}</em>'
        else:
            rendered = _render_md(r["content"] or "")
            body = f'<div class="content">{rendered}</div>'

        out += (
            f'<div class="{cls}">'
            f"<h3>{label}{badge}{meta}</h3>"
            f"{body}</div>"
        )

    for model_id in pending:
        label = _esc(MODEL_LABEL.get(model_id, model_id))

        out += (
            f'<div class="arena-card">'
            f"<h3>{label}</h3>"
            f"{SPINNER}</div>"
        )

    return out


def _format_evaluation(evaluation: dict, winner_id: str = "") -> str:
    if not evaluation or "error" in evaluation:
        msg = _esc(evaluation.get("error", "No evaluation."))
        return f"<p><em>{msg}</em></p>"

    winner_label = _esc(MODEL_LABEL.get(winner_id, winner_id))
    out = '<div class="eval-panel">'
    out += f"<h2>Winner: {winner_label}</h2>"

    for entry in evaluation.get("evaluations", []):
        label = _esc(MODEL_LABEL.get(entry["model"], entry["model"]))
        is_winner = entry["model"] == winner_id
        scores = entry.get("scores", {})

        accuracy = scores.get("accuracy", 0)
        conciseness = scores.get("conciseness", 0)
        tone = scores.get("tone", 0)
        speed = scores.get("speed", 0)

        try:
            total = accuracy + conciseness + tone + speed
        except TypeError:
            total = 0

        badge = '<span class="arena-badge">WINNER</span>' if is_winner else ""
        out += f"<h3>{label}{badge} — {total}/40</h3>"

        for criterion, score in [
            ("Accuracy", accuracy),
            ("Conciseness", conciseness),
            ("Tone", tone),
            ("Speed", speed),
        ]:
            if isinstance(score, (int, float)):
                pct = int((score / 10) * 100)
            else:
                pct = 0

            out += (
                f'<div style="display:flex;align-items:center;gap:8px;">'
                f'<span style="width:100px;font-size:0.85em;">'
                f"{criterion}</span>"
                f'<div class="score-bar-track" style="flex:1;">'
                f'<div class="score-bar-fill" style="width:{pct}%;">'
                f"</div></div>"
                f'<span style="font-size:0.85em;opacity:0.7;">'
                f"{score}/10</span></div>"
            )

        reasoning = entry.get("reasoning", "")

        if reasoning:
            out += (
                f'<p style="opacity:0.6;font-size:0.85em;margin-top:4px;">'
                f"<em>{_esc(reasoning)}</em></p>"
            )

    out += "</div>"

    return out


async def run_comparison(
    prompt: str,
    system_prompt: str,
    selected_models: list[str],
    judge_model: str,
):
    """Stream model responses as they arrive, then judge and display scores."""
    warn_template = (
        '<div style="border:1px solid #ef4444;'
        "border-radius:10px;padding:14px 18px;"
        "background:rgba(239,68,68,0.08);color:#fca5a5;font-weight:500;"
        '">{}</div>'
    )

    if not prompt.strip():
        msg = "Enter a prompt before running the arena."
        yield warn_template.format(msg), ""
        return

    if len(selected_models) < 2:
        msg = "Select at least 2 models to compare."
        yield warn_template.format(msg), ""
        return

    completed: dict[str, dict] = {}
    pending = list(selected_models)

    yield _format_responses(completed, pending), (
        '<div style="opacity:0.4;padding:16px;">'
        "Waiting for model responses...</div>"
    )

    async for model_id, result in run_arena_streaming(
        prompt, selected_models, system_prompt
    ):
        completed[model_id] = result
        pending = [m for m in selected_models if m not in completed]

        eval_placeholder = (
            '<div style="opacity:0.4;padding:16px;">'
            f"Received {len(completed)}/{len(selected_models)} responses..."
            "</div>"
        )

        if not pending:
            eval_placeholder = JUDGE_SPINNER

        yield _format_responses(completed, pending), eval_placeholder

    responses = [completed[m] for m in selected_models]
    evaluation = await evaluate_responses(prompt, responses, judge_model)
    winner_id = evaluation.get("winner", "")

    save_session(prompt, system_prompt, responses, evaluation)

    yield (
        _format_responses(completed, [], winner_id=winner_id),
        _format_evaluation(evaluation, winner_id=winner_id),
    )


def load_history_view() -> str:
    """Return HTML for the History tab from the last 30 sessions."""
    sessions = get_history(limit=30)

    if not sessions:
        return (
            '<p style="opacity:0.5;">No history. '
            "Run a comparison first.</p>"
        )

    out = ""

    for s in sessions:
        p = s["prompt"]
        short_prompt = _esc(p[:120] + "..." if len(p) > 120 else p)
        w = s.get("winner", "")

        winner_label = _esc(MODEL_LABEL.get(w, w or "\u2014"))
        model_names = (MODEL_LABEL.get(m, m) for m in s["models"])
        models_used = _esc(", ".join(model_names))

        evaluation = s.get("evaluation") or {}
        score_chips = ""

        for entry in evaluation.get("evaluations", []):
            elabel = _esc(MODEL_LABEL.get(entry["model"], entry["model"]))
            sc = entry.get("scores", {})

            try:
                t = sum(v for v in sc.values() if isinstance(v, (int, float)))
                max_score = len(sc) * 10
            except (TypeError, ValueError):
                t, max_score = 0, 40

            is_w = entry["model"] == w

            chip_style = (
                "background:rgba(99,102,241,0.15);color:#818cf8;"
                if is_w else "background:rgba(255,255,255,0.05);opacity:0.7;"
            )

            score_chips += (
                f'<span class="hist-chip" style="{chip_style}">'
                f"{elabel}: {t}/{max_score}</span>"
            )

        ts = s["created_at"].replace("T", " ").split("+")[0]

        out += (
            f'<div class="hist-card">'
            f'<p class="hist-prompt">{short_prompt}'
            f'<span class="hist-winner">{winner_label}</span></p>'
            f'<div style="margin-top:6px;">{score_chips}</div>'
            f'<div class="hist-meta">'
            f"<span>{_esc(ts)}</span>"
            f"<span>{models_used}</span>"
            f"</div></div>"
        )

    return out


def _reset_session():
    """Clear the current session outputs and restore default inputs."""
    return (
        DEFAULT_SYSTEM_PROMPT,
        DEFAULT_PROMPT,
        DEFAULT_MODELS,
        JUDGE_MODEL,
        "",
        "",
    )


def _clear_history_and_reload():
    """Wipe the DB and return empty history view."""
    clear_history()
    return load_history_view()


def _shutdown():
    """Gracefully stop the Gradio server."""
    os.kill(os.getpid(), signal.SIGTERM)


with gr.Blocks(
    title="Model Arena",
    theme=gr.themes.Soft(),
    css=CSS,
) as app:
    gr.Markdown(
        "# Model Arena\n"
        "Send a prompt to multiple language models at once and let GPT-4o "
        "elect the winner."
    )

    with gr.Tabs() as tabs:
        with gr.Tab("Arena"):
            system_prompt_input = gr.Textbox(
                label="System Prompt (optional)",
                value=DEFAULT_SYSTEM_PROMPT,
                lines=2,
            )

            prompt_input = gr.Textbox(
                label="Prompt",
                value=DEFAULT_PROMPT,
                lines=3,
            )

            model_selector = gr.CheckboxGroup(
                choices=MODEL_CHOICES,
                value=DEFAULT_MODELS,
                label="Models to compare",
            )

            judge_selector = gr.Dropdown(
                choices=MODEL_CHOICES,
                value=JUDGE_MODEL,
                label="Judge model",
            )

            with gr.Row():
                run_btn = gr.Button("Run Arena", variant="primary", scale=3)

                clear_btn = gr.Button(
                    "Clear Session", variant="secondary", scale=1
                )

                stop_btn = gr.Button("Stop Server", variant="stop", scale=1)

            responses_out = gr.HTML(label="Responses")
            eval_out = gr.HTML(label="Evaluation")

            # pylint: disable-next=no-member
            run_btn.click(
                fn=run_comparison,
                inputs=[
                    prompt_input,
                    system_prompt_input,
                    model_selector,
                    judge_selector,
                ],
                outputs=[responses_out, eval_out],
            )

            # pylint: disable-next=no-member
            clear_btn.click(
                fn=_reset_session,
                outputs=[
                    system_prompt_input,
                    prompt_input,
                    model_selector,
                    judge_selector,
                    responses_out,
                    eval_out,
                ],
            )

            # pylint: disable-next=no-member
            stop_btn.click(fn=_shutdown)

        with gr.Tab("History") as history_tab:
            with gr.Row():
                refresh_btn = gr.Button("Refresh", scale=3)

                clear_hist_btn = gr.Button(
                    "Clear History", variant="stop", scale=1,
                )

            history_out = gr.HTML()

            # pylint: disable-next=no-member
            refresh_btn.click(fn=load_history_view, outputs=history_out)

            # pylint: disable-next=no-member
            clear_hist_btn.click(
                fn=_clear_history_and_reload,
                outputs=history_out,
            )

            # pylint: disable-next=no-member
            history_tab.select(fn=load_history_view, outputs=history_out)


if __name__ == "__main__":
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
    )
