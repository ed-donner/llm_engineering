"""
app.py
------
Gradio UI for the Multi-Agent Research System.
API keys are loaded from .env only — no key inputs in the UI.

Run:
    python app.py
"""

from __future__ import annotations

import logging
import tempfile

import gradio as gr

from agents.base import EventType, format_log_line
from config import config
from orchestrator import MultiAgentOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Agent metadata ────────────────────────────────────────────────────────────
AGENTS_META = [
    {"name": "Claude",  "provider": "Anthropic",  "model": "claude-sonnet-4", "color": "#da7756"},
    {"name": "GPT-4o",  "provider": "OpenAI",     "model": "gpt-4o",          "color": "#10a37f"},
    {"name": "Gemini",  "provider": "OpenRouter",  "model": "gemini-2.0-flash","color": "#4285f4"},
]

# ── CSS ────────────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

body, .gradio-container {
    font-family: 'IBM Plex Sans', sans-serif !important;
    background: #07090f !important;
    color: #c9d1d9 !important;
}
.mas-header {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 24px 32px 18px;
    margin-bottom: 6px;
}
.mas-header h1 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 20px !important; font-weight: 600 !important;
    color: #e6edf3 !important; margin: 0 0 4px !important; letter-spacing: 1px;
}
.mas-header p { color: #8b949e !important; font-size: 12px !important; margin: 0 !important; }
.accent-bar {
    height: 2px;
    background: linear-gradient(90deg, #da7756, #10a37f, #4285f4, #a371f7);
    border-radius: 2px; margin-bottom: 20px;
}
.agent-card-header {
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid #21262d;
}
.agent-dot  { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.agent-name { font-family: 'IBM Plex Mono', monospace; font-size: 12px; font-weight: 600; color: #e6edf3; }
.agent-model{ font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: #484f58; margin-left: auto; }
.status-badge { font-family:'IBM Plex Mono',monospace; font-size:9px; letter-spacing:2px;
                padding:3px 8px; border-radius:3px; display:inline-block; }
.status-idle    { background:#161b22; color:#484f58; border:1px solid #21262d; }
.status-running { background:#1f2d1a; color:#3fb950; border:1px solid #238636; }
.status-done    { background:#1a2d1f; color:#3fb950; border:1px solid #2ea043; }
.status-error   { background:#2d1a1a; color:#f85149; border:1px solid #da3633; }
.agent-log {
    font-family: 'IBM Plex Mono', monospace !important; font-size: 11px !important;
    color: #8b949e !important; min-height: 240px !important; max-height: 300px !important;
    overflow-y: auto !important; background: #090f1a !important;
    border: 1px solid #161b22 !important; border-radius: 6px !important; padding: 12px 14px !important;
}
.query-row textarea {
    font-family: 'IBM Plex Sans', sans-serif !important; font-size: 14px !important;
    background: #0d1117 !important; border: 1px solid #30363d !important;
    border-radius: 6px !important; color: #e6edf3 !important;
}
.query-row textarea:focus { border-color: #a371f7 !important; box-shadow: 0 0 0 3px rgba(163,113,247,.12) !important; }
#run-btn {
    background: #6e40c9 !important; border: 1px solid #8957e5 !important; color: #fff !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 12px !important;
    font-weight: 600 !important; border-radius: 6px !important;
}
#run-btn:hover { background: #8957e5 !important; }
#clear-btn {
    background: #161b22 !important; border: 1px solid #30363d !important; color: #8b949e !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 12px !important; border-radius: 6px !important;
}
#synthesis-report {
    background: #0d1117 !important; border: 1px solid #30363d !important;
    border-radius: 8px !important; padding: 28px 32px !important;
    min-height: 200px !important; font-size: 14px !important; line-height: 1.8 !important;
}
#synthesis-report h1 { color: #e6edf3 !important; font-size: 20px !important; font-weight: 600 !important; }
#synthesis-report h2 {
    color: #a371f7 !important; font-size: 11px !important; text-transform: uppercase;
    letter-spacing: 3px; margin-top: 24px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    border-bottom: 1px solid #21262d; padding-bottom: 6px;
}
#synthesis-report strong { color: #f0883e !important; }
#synthesis-report hr { border-color: #21262d !important; }
#stats-bar {
    background: #161b22 !important; border: 1px solid #21262d !important;
    border-radius: 6px !important; padding: 8px 14px !important;
    font-size: 11px !important; color: #8b949e !important;
    font-family: 'IBM Plex Mono', monospace !important;
}
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #21262d; border-radius: 2px; }
"""


# ── Helpers ───────────────────────────────────────────────────────────────────
def _agent_header_html(idx: int, status: str = "IDLE") -> str:
    m = AGENTS_META[idx]
    css = {"IDLE":"status-idle","RUNNING":"status-running","DONE":"status-done","ERROR":"status-error"}.get(status,"status-idle")
    return (
        f'<div class="agent-card-header">'
        f'<div class="agent-dot" style="background:{m["color"]};box-shadow:0 0 6px {m["color"]}88"></div>'
        f'<span class="agent-name">{m["name"]}</span>'
        f'<span class="agent-model">{m["provider"]} · {m["model"]}</span>'
        f'<span class="status-badge {css}">{status}</span>'
        f'</div>'
    )


# ── Streaming research function ───────────────────────────────────────────────
def run_research(query: str):
    """
    Yields 9-tuples: header0, log0, header1, log1, header2, log2,
                     synthesis_md, stats_md, dl_btn
    """
    if not query.strip():
        yield (
            gr.update(), "⚠️ Please enter a research query.",
            gr.update(), gr.update(),
            gr.update(), gr.update(),
            gr.update(), gr.update(), gr.update(visible=False),
        )
        return

    # Validate keys loaded from .env
    missing = []
    if not config.anthropic_api_key:  missing.append("ANTHROPIC_API_KEY")
    if not config.openai_api_key:     missing.append("OPENAI_API_KEY")
    if not config.openrouter_api_key: missing.append("OPENROUTER_API_KEY")
    if missing:
        yield (
            gr.update(), f"❌ Missing keys in `.env`: {', '.join(missing)}",
            gr.update(), gr.update(),
            gr.update(), gr.update(),
            gr.update(), gr.update(), gr.update(visible=False),
        )
        return

    # Initial state
    logs     = ["*Starting…*", "*Starting…*", "*Starting…*"]
    headers  = [_agent_header_html(i, "RUNNING") for i in range(3)]
    statuses = ["RUNNING", "RUNNING", "RUNNING"]
    line_idx = [0, 0, 0]

    yield (
        headers[0], logs[0],
        headers[1], logs[1],
        headers[2], logs[2],
        "⏳ Waiting for all 3 agents to complete…",
        "", gr.update(visible=False),
    )

    orchestrator = MultiAgentOrchestrator()

    for agent_id, event in orchestrator.run(query):

        if agent_id < 3:
            # ── Research agent update ─────────────────────────────────────────
            line_idx[agent_id] += 1
            line = format_log_line(event, line_idx[agent_id])
            logs[agent_id] = (line if logs[agent_id] == "*Starting…*"
                              else logs[agent_id] + "\n\n" + line)

            if event.event_type == EventType.COMPLETE:
                statuses[agent_id] = "DONE"
                headers[agent_id]  = _agent_header_html(agent_id, "DONE")
            elif event.event_type == EventType.ERROR:
                statuses[agent_id] = "ERROR"
                headers[agent_id]  = _agent_header_html(agent_id, "ERROR")

            yield (
                headers[0], logs[0],
                headers[1], logs[1],
                headers[2], logs[2],
                "⏳ Waiting for all 3 agents to complete…",
                "", gr.update(visible=False),
            )

        else:
            # ── Synthesis agent update ────────────────────────────────────────
            if event.event_type == EventType.COMPLETE:
                synth   = orchestrator._synthesis
                md      = synth.markdown
                report  = synth.report

                # Write plain-text download file
                tmp = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".txt",
                    prefix="synthesis_report_",
                    mode="w", encoding="utf-8",
                )
                tmp.write(synth.plain_text)
                tmp.close()

                stats = (
                    f"**Agents:** {sum(1 for s in statuses if s=='DONE')}/3 succeeded"
                    f" &nbsp;|&nbsp; **Consensus:** {len(report.consensus) if report else 0}"
                    f" &nbsp;|&nbsp; **Disagreements:** {len(report.disagreements) if report else 0}"
                    f" &nbsp;|&nbsp; **Findings:** {report.finding_count if report else 0}"
                )

                yield (
                    headers[0], logs[0],
                    headers[1], logs[1],
                    headers[2], logs[2],
                    md,
                    stats,
                    gr.update(value=tmp.name, visible=True),
                )

            elif event.event_type == EventType.ERROR:
                yield (
                    headers[0], logs[0],
                    headers[1], logs[1],
                    headers[2], logs[2],
                    f"## ❌ Synthesis Failed\n\n{event.message}",
                    "", gr.update(visible=False),
                )
            else:
                yield (
                    headers[0], logs[0],
                    headers[1], logs[1],
                    headers[2], logs[2],
                    f"⚗️ {event.message}",
                    gr.update(), gr.update(),
                )


def clear_all():
    headers = [_agent_header_html(i, "IDLE") for i in range(3)]
    return (
        "",
        headers[0], "*Agent log will stream here…*",
        headers[1], "*Agent log will stream here…*",
        headers[2], "*Agent log will stream here…*",
        "Synthesis report will appear here after all agents complete.",
        "", gr.update(visible=False),
    )


# ── Build UI ──────────────────────────────────────────────────────────────────
def build_app() -> gr.Blocks:
    with gr.Blocks(title=config.app_title) as demo:

        gr.HTML("""
            <div class="mas-header">
                <h1>⬡ MULTI-AGENT RESEARCH SYSTEM</h1>
                <p>3 parallel AI analysts · Claude × GPT-4o × Gemini · GPT-4o Synthesis</p>
            </div>
            <div class="accent-bar"></div>
        """)

        # Query input — no API key fields
        with gr.Row(elem_classes="query-row"):
            query_input = gr.Textbox(
                placeholder='Enter your research query, e.g. "What are the main causes of poverty in the world?"',
                label="Research Query", lines=2, scale=5, show_label=False,
            )
        with gr.Row():
            run_btn   = gr.Button("▶  Run Multi-Agent Research", elem_id="run-btn",   scale=3)
            clear_btn = gr.Button("✕  Clear",                    elem_id="clear-btn", scale=1)

        # ── 3 Agent panels ────────────────────────────────────────────────────
        gr.HTML('<div style="font-family:\'IBM Plex Mono\',monospace;font-size:9px;'
                'letter-spacing:4px;color:#30363d;margin:16px 0 10px;">'
                'RESEARCH AGENTS — RUNNING IN PARALLEL</div>')

        with gr.Row(equal_height=False):
            with gr.Column():
                header_0 = gr.HTML(_agent_header_html(0, "IDLE"))
                log_0    = gr.Markdown("*Agent log will stream here…*", elem_classes="agent-log")
            with gr.Column():
                header_1 = gr.HTML(_agent_header_html(1, "IDLE"))
                log_1    = gr.Markdown("*Agent log will stream here…*", elem_classes="agent-log")
            with gr.Column():
                header_2 = gr.HTML(_agent_header_html(2, "IDLE"))
                log_2    = gr.Markdown("*Agent log will stream here…*", elem_classes="agent-log")

        # ── Synthesis report ──────────────────────────────────────────────────
        gr.HTML('<div style="font-family:\'IBM Plex Mono\',monospace;font-size:9px;'
                'letter-spacing:4px;color:#a371f744;margin:20px 0 10px;'
                'border-top:1px solid #21262d;padding-top:16px;">'
                '⚗ SYNTHESIS REPORT — GPT-4o UNIFIED INTELLIGENCE</div>')

        stats_md     = gr.Markdown("", elem_id="stats-bar")
        synthesis_md = gr.Markdown(
            "Synthesis report will appear here after all agents complete.",
            elem_id="synthesis-report",
        )
        dl_btn = gr.File(label="⬇  Download Synthesis Report (.txt)", visible=False)

        # Examples
        gr.HTML('<div style="font-family:\'IBM Plex Mono\',monospace;font-size:9px;'
                'letter-spacing:3px;color:#30363d;margin-top:20px;">EXAMPLE QUERIES</div>')
        gr.Examples(
            examples=[
                ["What are the main causes of poverty in the world?"],
                ["How is generative AI changing the software engineering job market?"],
                ["What are the latest developments in nuclear fusion energy?"],
                ["What caused the 2008 global financial crisis?"],
            ],
            inputs=query_input, label="",
        )

        gr.HTML('<p style="text-align:center;color:#21262d;font-size:11px;'
                'font-family:\'IBM Plex Mono\',monospace;margin-top:24px;">'
                'Multi-Agent Research System · Claude · GPT-4o · Gemini · GPT-4o Synthesis</p>')

        # ── Wiring ────────────────────────────────────────────────────────────
        all_outputs = [
            header_0, log_0,
            header_1, log_1,
            header_2, log_2,
            synthesis_md, stats_md, dl_btn,
        ]

        run_btn.click(
            fn=run_research,
            inputs=[query_input],
            outputs=all_outputs,
            show_progress="minimal",
        )
        query_input.submit(
            fn=run_research,
            inputs=[query_input],
            outputs=all_outputs,
            show_progress="minimal",
        )
        clear_btn.click(
            fn=clear_all,
            outputs=[query_input] + all_outputs,
        )

    return demo


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = build_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=config.server_port,
        share=config.share,
        show_error=True,
        inbrowser=True,
        css=CUSTOM_CSS,
        theme=gr.themes.Base(
            primary_hue="purple",
            neutral_hue="slate",
            font=gr.themes.GoogleFont("IBM Plex Sans"),
        ),
    )
