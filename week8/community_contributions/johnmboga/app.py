"""
app.py
Job Fit Alert Agent — Gradio UI
Orchestrates all agents and provides a clean monitoring dashboard.
"""

import time
import threading
from pathlib import Path

import gradio as gr
from core.cache import SeenJobsCache
from core.orchestrator import Orchestrator
from agents.scorer import Scorer

_cache = SeenJobsCache()
_scorer = Scorer()
orchestrator = Orchestrator(cache=_cache, scorer=_scorer)

print("Preloading embedding model...")
threading.Thread(target=_scorer.preload_model, daemon=True).start()

DEFAULT_FEEDS = "\n".join([
    "https://remoteok.com/remote-jobs.rss",
    "https://weworkremotely.com/remote-jobs.rss",
])

_CSS_PATH = Path(__file__).resolve().parent / "static" / "styles.css"
CSS = _CSS_PATH.read_text(encoding="utf-8")

def _status_html() -> str:
    s = orchestrator.state
    dot_class = "dot running" if s["running"] else "dot stopped"
    status_text = s["status"]
    last = s["last_check"] or "—"
    return f"""
<div class="status-bar">
    <div class="stat-item">
        <div class="stat-value">{s['jobs_scanned']}</div>
        <div class="stat-label">Jobs Scanned</div>
    </div>
    <div class="stat-item">
        <div class="stat-value" style="color:var(--accent2)">{s['alerts_sent']}</div>
        <div class="stat-label">Alerts Sent</div>
    </div>
    <div class="stat-item">
        <div class="stat-value" style="color:var(--warn)">{len(s['matches'])}</div>
        <div class="stat-label">Matches Found</div>
    </div>
    <div class="stat-item">
        <div class="stat-value" style="font-size:1rem;color:var(--muted)">{last}</div>
        <div class="stat-label">Last Check</div>
    </div>
    <div class="status-indicator">
        <div class="{dot_class}"></div>
        <span style="color:var(--text)">{status_text}</span>
    </div>
</div>"""


def _matches_html() -> str:
    matches = orchestrator.state["matches"]
    if not matches:
        return '<div style="color:var(--muted);font-family:\'DM Mono\',monospace;font-size:0.85rem;padding:1rem 0;">No matches yet. Agent is monitoring feeds...</div>'
    
    cards = []
    for m in matches[:10]:
        cards.append(f"""
<div class="match-card">
    <div class="match-title">{m['title']}</div>
    <div class="match-company">{m['company']} · {m.get('time','')}</div>
    <div class="match-score">⚡ {m['score']}% FIT</div>
    <div class="match-summary">{m.get('summary','')}</div>
    <a class="match-link" href="{m['url']}" target="_blank">→ View listing</a>
</div>""")
    return "".join(cards)


def _log_html() -> str:
    logs = orchestrator.state["logs"]
    if not logs:
        return '<div class="log-box">Waiting for agent to start...</div>'
    lines = "<br>".join(logs[:40])
    return f'<div class="log-box">{lines}</div>'


def _all_jobs_md() -> str:
    jobs = orchestrator.state["all_jobs"]
    if not jobs:
        return "_No jobs scanned yet._"
    rows = ["| Time | Title | Company | Fit Score | Match |",
            "|------|-------|---------|-----------|-------|"]
    for j in jobs[:50]:
        flag = "✅" if j["matched"] else "—"
        rows.append(f"| {j['time']} | {j['title'][:40]} | {j['company'][:25]} | {j['score']}% | {flag} |")
    return "\n".join(rows)


def start_agent(name, cv, prefs, threshold, feeds_text, interval):
    if not cv.strip():
        return "⚠️ Please paste your CV before starting.", *_refresh_ui()
    if not name.strip():
        return "⚠️ Please enter your name.", *_refresh_ui()

    feeds = [f.strip() for f in feeds_text.strip().splitlines() if f.strip()]
    if not feeds:
        return "⚠️ Add at least one RSS feed URL.", *_refresh_ui()

    orchestrator.start(
        cv_text=cv,
        preferences=prefs,
        threshold=threshold / 100,
        rss_feeds=feeds,
        seeker_name=name,
        interval_minutes=int(interval),
    )
    time.sleep(0.5)
    return "✅ Agent started!", *_refresh_ui()


def stop_agent():
    orchestrator.stop()
    time.sleep(0.5)
    return "⏹ Agent stopped.", *_refresh_ui()


def reset_agent():
    orchestrator.reset()
    time.sleep(0.5)
    return "🔄 Reset complete.", *_refresh_ui()


def _refresh_ui():
    return (
        _status_html(),
        _matches_html(),
        _log_html(),
        _all_jobs_md(),
    )


def refresh_ui():
    return _refresh_ui()


with gr.Blocks(title="Job Fit Agent") as demo:

    gr.HTML("""
    <div class="app-header">
        <h1>⚡ Job Fit Agent</h1>
        <p>Agentic AI that monitors job feeds and alerts you when the right opportunity appears</p>
    </div>
    """)

    msg_box = gr.Textbox(
        label="", placeholder="Status messages appear here...",
        interactive=False, visible=False,
    )

    with gr.Row():
        with gr.Column(scale=4):
            gr.HTML('<div class="panel-title">01 — Your Profile</div>')

            seeker_name = gr.Textbox(
                label="Your Name",
                placeholder="e.g. John Mboga",
            )
            cv_text = gr.Textbox(
                label="CV / Profile",
                placeholder="Paste your full CV or a summary of your skills, experience, and background...",
                lines=10,
            )
            preferences = gr.Textbox(
                label="Job Preferences (optional)",
                placeholder="e.g. Remote ML engineer roles, Python, fintech, East Africa preferred...",
                lines=3,
            )

            gr.HTML('<div class="panel-title" style="margin-top:1.5rem">02 — Agent Settings</div>')

            threshold = gr.Slider(
                minimum=30, maximum=95, value=60, step=5,
                label="Fit Score Threshold (%)",
                info="Only alert when similarity score exceeds this value",
            )
            interval = gr.Number(
                value=5, minimum=1, maximum=60,
                label="Check Interval (minutes)",
            )

            gr.HTML('<div class="panel-title" style="margin-top:1.5rem">03 — RSS Feeds</div>')
            feeds_text = gr.Textbox(
                label="Feed URLs (one per line)",
                value=DEFAULT_FEEDS,
                lines=4,
                info="Add any job board RSS feed URLs",
            )

            with gr.Row():
                btn_start = gr.Button("▶ START MONITORING", elem_classes=["btn-start"])
                btn_stop  = gr.Button("⏹ STOP",  elem_classes=["btn-stop"])
            btn_reset = gr.Button("↺ Reset Session", elem_classes=["btn-reset"])

        with gr.Column(scale=6):
            gr.HTML('<div class="panel-title">Live Status</div>')
            status_html = gr.HTML(_status_html())

            with gr.Tabs():
                with gr.Tab("🎯 Matches"):
                    gr.HTML('<div class="panel-title">Jobs That Match Your Profile</div>')
                    matches_html = gr.HTML(_matches_html())

                with gr.Tab("📋 All Scanned Jobs"):
                    all_jobs_md = gr.Markdown(_all_jobs_md())

                with gr.Tab("📡 Activity Log"):
                    log_html = gr.HTML(_log_html())

            refresh_btn = gr.Button("🔄 Refresh", size="sm")

    outputs = [status_html, matches_html, log_html, all_jobs_md]

    btn_start.click(
        fn=start_agent,
        inputs=[seeker_name, cv_text, preferences, threshold, feeds_text, interval],
        outputs=[msg_box, *outputs],
    )
    btn_stop.click(fn=stop_agent, outputs=[msg_box, *outputs])
    btn_reset.click(fn=reset_agent, outputs=[msg_box, *outputs])
    refresh_btn.click(fn=refresh_ui, outputs=outputs)

    timer = gr.Timer(value=8, active=True)
    timer.tick(fn=refresh_ui, outputs=outputs)


if __name__ == "__main__":
    import socket
    def find_free_port(start=7860, end=7960):
        for port in range(start, end):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("localhost", port)) != 0:
                    return port
        raise OSError("No free port found in range.")
    server_port = find_free_port()
    print(f"Starting server on port {server_port}")
    demo.launch(
        server_port=server_port,
        share=False,
        show_error=True,
        css=CSS,
    )
