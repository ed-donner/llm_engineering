"""Gradio dashboard for the AI Financial News Analyst.

The pipeline runs automatically every 10 minutes in the background.
No user interaction is required — results show in the dashboard and pushover notifications sent to user phone.

"""

from __future__ import annotations

#imports
from dotenv import load_dotenv
load_dotenv(override=True)

import logging
import time

import gradio as gr

from config import APP_CONFIG
from orchestrator import AnalysisResult
from scheduler import NewsScheduler, get_results, get_status

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

#validate & start scheduler
APP_CONFIG.validate()
_scheduler = NewsScheduler()
_scheduler.start()


#badge helpers
def _sentiment_badge(label: str, score: float) -> str:
    colour = {"positive": "#22c55e", "negative": "#ef4444", "neutral": "#f59e0b"}
    bg = colour.get(label, "#6b7280")
    return (
        f'<span style="background:{bg};color:#fff;padding:3px 12px;'
        f'border-radius:9999px;font-weight:700;font-size:.8rem;">'
        f"{label.upper()} {score:.0%}</span>"
    )

def _safeguard_badge(verdict: str) -> str:
    colour = {"PASS": "#22c55e", "WARN": "#f59e0b", "FAIL": "#ef4444"}
    bg = colour.get(verdict, "#6b7280")
    return (
        f'<span style="background:{bg};color:#fff;padding:3px 12px;'
        f'border-radius:9999px;font-weight:700;font-size:.8rem;">'
        f"{verdict}</span>"
    )

def _notif_badge(sent: bool) -> str:
    if sent:
        return '<span style="background:#7c3aed;color:#fff;padding:3px 10px;border-radius:9999px;font-size:.8rem;">🔔 Notified</span>'
    return '<span style="background:#1d2e45;color:#64748b;padding:3px 10px;border-radius:9999px;font-size:.8rem;">silent</span>'


#result card renderer

def _render_result_card(r: AnalysisResult) -> str:
    tools_html = " → ".join(
        f'<code style="background:#0a1e35;color:#38bdf8;padding:1px 5px;'
        f'border-radius:3px;font-size:.65rem;">{t}</code>'
        for t in r.tool_calls_made
    )
    flags_html = ""
    if r.safeguard_flags:
        flags_html = "<br>".join(f"⚑ {f}" for f in r.safeguard_flags)
        flags_html = (
            f'<div style="font-size:.72rem;color:#f59e0b;margin-top:6px;">{flags_html}</div>'
        )

    brief_preview = (r.investment_brief or "")[:600].replace("\n", "<br>")
    if len(r.investment_brief or "") > 600:
        brief_preview += "…"

    return f"""
    <div style="background:#0f1824;border:1px solid #1d2e45;border-radius:10px;
                padding:16px 18px;margin-bottom:12px;">

      <!-- Header row -->
      <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;
                  margin-bottom:10px;">
        <span style="font-size:.85rem;font-weight:700;color:#e2e8f0;flex:1;min-width:0;">
          {r.headline[:120]}
        </span>
        <div style="display:flex;gap:6px;align-items:center;flex-shrink:0;">
          {_sentiment_badge(r.sentiment_label, r.sentiment_score) if r.sentiment_label else ""}
          {_safeguard_badge(r.safeguard_verdict) if r.safeguard_verdict else ""}
          {_notif_badge(r.notification_sent)}
        </div>
      </div>

      <!-- Meta -->
      <div style="font-size:.7rem;color:#475569;font-family:'IBM Plex Mono',monospace;
                  margin-bottom:8px;">
        {r.source} · {r.published_at[:16]}
      </div>

      <!-- Tool call chain -->
      <div style="margin-bottom:10px;line-height:1.8;">{tools_html}</div>

      <!-- Brief preview -->
      <div style="font-size:.8rem;color:#94a3b8;line-height:1.65;
                  border-top:1px solid #1d2e45;padding-top:10px;">
        {brief_preview}
      </div>

      {flags_html}

    </div>"""


def load_dashboard():
    """
    Called by Gradio every 30 seconds via gr.Timer, and on manual refresh.
    Returns: (status_html, results_html, stats_html)
    """
    status   = get_status()
    results  = get_results()

    #status bar
    running_indicator = (
        '<span style="color:#38bdf8;animation:blink 1s infinite;">⏳ Running…</span>'
        if status["is_running"]
        else '<span style="color:#22c55e;">✅ Idle</span>'
    )
    status_html = f"""
    <div style="background:#0f1824;border:1px solid #1d2e45;border-radius:8px;
                padding:10px 16px;font-family:'IBM Plex Mono',monospace;font-size:.75rem;
                display:flex;gap:24px;flex-wrap:wrap;color:#64748b;">
      <span>Status: {running_indicator}</span>
      <span>Last run: <span style="color:#94a3b8;">{status['last_run']}</span></span>
      <span>Articles analysed: <span style="color:#94a3b8;">{status['total_results']}</span></span>
      <span>Next run: every <span style="color:#94a3b8;">{APP_CONFIG.news.interval_minutes} min</span></span>
    </div>"""

    #stats
    if results:
        pos   = sum(1 for r in results if r.sentiment_label == "positive")
        neg   = sum(1 for r in results if r.sentiment_label == "negative")
        neu   = sum(1 for r in results if r.sentiment_label == "neutral")
        fails = sum(1 for r in results if r.safeguard_verdict == "FAIL")
        warns = sum(1 for r in results if r.safeguard_verdict == "WARN")
        notif = sum(1 for r in results if r.notification_sent)
        stats_html = f"""
        <div style="display:flex;gap:12px;flex-wrap:wrap;margin:8px 0;">
          <div style="background:#0f1824;border:1px solid #22c55e33;border-radius:8px;
                      padding:10px 16px;text-align:center;min-width:80px;">
            <div style="font-size:1.4rem;font-weight:900;color:#22c55e;">{pos}</div>
            <div style="font-size:.65rem;color:#475569;font-family:'IBM Plex Mono',monospace;">POSITIVE</div>
          </div>
          <div style="background:#0f1824;border:1px solid #ef444433;border-radius:8px;
                      padding:10px 16px;text-align:center;min-width:80px;">
            <div style="font-size:1.4rem;font-weight:900;color:#ef4444;">{neg}</div>
            <div style="font-size:.65rem;color:#475569;font-family:'IBM Plex Mono',monospace;">NEGATIVE</div>
          </div>
          <div style="background:#0f1824;border:1px solid #f59e0b33;border-radius:8px;
                      padding:10px 16px;text-align:center;min-width:80px;">
            <div style="font-size:1.4rem;font-weight:900;color:#f59e0b;">{neu}</div>
            <div style="font-size:.65rem;color:#475569;font-family:'IBM Plex Mono',monospace;">NEUTRAL</div>
          </div>
          <div style="background:#0f1824;border:1px solid #ef444433;border-radius:8px;
                      padding:10px 16px;text-align:center;min-width:80px;">
            <div style="font-size:1.4rem;font-weight:900;color:#ef4444;">{fails}</div>
            <div style="font-size:.65rem;color:#475569;font-family:'IBM Plex Mono',monospace;">SAFEGUARD FAIL</div>
          </div>
          <div style="background:#0f1824;border:1px solid #f59e0b33;border-radius:8px;
                      padding:10px 16px;text-align:center;min-width:80px;">
            <div style="font-size:1.4rem;font-weight:900;color:#f59e0b;">{warns}</div>
            <div style="font-size:.65rem;color:#475569;font-family:'IBM Plex Mono',monospace;">SAFEGUARD WARN</div>
          </div>
          <div style="background:#0f1824;border:1px solid #7c3aed33;border-radius:8px;
                      padding:10px 16px;text-align:center;min-width:80px;">
            <div style="font-size:1.4rem;font-weight:900;color:#a78bfa;">{notif}</div>
            <div style="font-size:.65rem;color:#475569;font-family:'IBM Plex Mono',monospace;">NOTIFICATIONS</div>
          </div>
        </div>"""
    else:
        stats_html = (
            '<div style="color:#475569;font-size:.8rem;font-family:\'IBM Plex Mono\',monospace;">'
            'Waiting for first analysis cycle…</div>'
        )

    #result cards (newest first, max 50)
    if results:
        cards = "".join(_render_result_card(r) for r in results[:50])
    else:
        cards = (
            '<div style="color:#475569;text-align:center;padding:40px;'
            'font-family:\'IBM Plex Mono\',monospace;font-size:.8rem;">'
            '⏳ First analysis cycle is running… check back in a moment.</div>'
        )

    return status_html, stats_html, cards


def manual_run():
    """Trigger an immediate analysis cycle from the UI."""
    _scheduler.run_now()
    time.sleep(0.5)
    return load_dashboard()


#css, fonts

_CSS = """
:root {
    --bg:      #080d18;
    --surf:    #0f1824;
    --border:  #1d2e45;
    --accent:  #38bdf8;
    --accent2: #818cf8;
    --text:    #e2e8f0;
    --muted:   #64748b;
    --mono:    'IBM Plex Mono', 'Fira Code', monospace;
    --sans:    'DM Sans', 'Segoe UI', sans-serif;
}
body, .gradio-container {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
}
#hdr { text-align:center; padding:2rem 0 1.2rem; border-bottom:1px solid var(--border); margin-bottom:1.2rem; }
#hdr h1 { font-size:2.1rem; font-weight:900; letter-spacing:-0.04em;
          background:linear-gradient(90deg,var(--accent),var(--accent2));
          -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0; }
#hdr p { color:var(--muted); font-size:.78rem; font-family:var(--mono); margin:.35rem 0 0; }
.gr-box, .gr-panel, .gr-form, .gr-block {
    background:var(--surf) !important; border:1px solid var(--border) !important; border-radius:10px !important;
}
button.primary {
    background:linear-gradient(135deg,var(--accent),var(--accent2)) !important;
    border:none !important; color:#fff !important; font-weight:800 !important;
    border-radius:8px !important; padding:10px 28px !important; transition:opacity .2s;
}
button.primary:hover { opacity:.85; }
button.secondary {
    background:#0f1824 !important; border:1px solid var(--border) !important;
    color:var(--muted) !important; border-radius:8px !important;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.4} }
.section-label {
    font-family:var(--mono); font-size:.68rem; text-transform:uppercase;
    letter-spacing:.1em; color:var(--muted); margin:.8rem 0 .3rem;
}
"""

_HEAD = """
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700;900&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet"/>
"""

#UI

with gr.Blocks(css=_CSS, head=_HEAD, title="AI Financial News Analyst") as demo:

    
    gr.HTML("""
    <div id="hdr">
      <h1>AI Financial News Analyst</h1>
      <p>Autonomous · Claude orchestrates tool calls every 10 min · Pushover alerts on your phone</p>
    </div>
    """)

    
    gr.HTML("""
    <div style="background:#0f1824;border:1px solid #1d2e45;border-radius:10px;
                padding:16px 20px;margin-bottom:1rem;font-family:'IBM Plex Mono',monospace;">
      <div style="font-size:.65rem;text-transform:uppercase;letter-spacing:.1em;
                  color:#64748b;margin-bottom:10px;">⚙️ How It Works</div>
      <div style="display:flex;align-items:center;flex-wrap:wrap;gap:5px;margin-bottom:12px;">
        <span style="background:#0a1e35;border:1px solid #1d2e45;color:#38bdf8;padding:4px 10px;border-radius:5px;font-size:.7rem;">📡 Finnhub<br><span style="color:#475569;font-size:.62rem;">top 20 news</span></span>
        <span style="color:#334155;">→</span>
        <span style="background:#0a1e35;border:1px solid #1d2e45;color:#818cf8;padding:4px 10px;border-radius:5px;font-size:.7rem;">🧠 Claude<br><span style="color:#475569;font-size:.62rem;">orchestrator</span></span>
        <span style="color:#334155;">→</span>
        <span style="background:#0a1e35;border:1px solid #1d2e45;color:#a78bfa;padding:4px 10px;border-radius:5px;font-size:.7rem;">🤖 get_sentiment<br><span style="color:#475569;font-size:.62rem;">DistilRoberta local</span></span>
        <span style="color:#334155;">→</span>
        <span style="background:#0a1e35;border:1px solid #1d2e45;color:#818cf8;padding:4px 10px;border-radius:5px;font-size:.7rem;">🗄️ get_rag_context<br><span style="color:#475569;font-size:.62rem;">ChromaDB</span></span>
        <span style="color:#334155;">→</span>
        <span style="background:#0a1e35;border:1px solid #1d2e45;color:#34d399;padding:4px 10px;border-radius:5px;font-size:.7rem;">⚔️ cross_check<br><span style="color:#475569;font-size:.62rem;">GPT-4o</span></span>
        <span style="color:#334155;">→</span>
        <span style="background:#0a1e35;border:1px solid #1d2e45;color:#fb923c;padding:4px 10px;border-radius:5px;font-size:.7rem;">🛡️ safeguard_check<br><span style="color:#475569;font-size:.62rem;">GPT-4o JSON</span></span>
        <span style="color:#334155;">→</span>
        <span style="background:#0a1e35;border:1px solid #1d2e45;color:#38bdf8;padding:4px 10px;border-radius:5px;font-size:.7rem;">📋 write_brief<br><span style="color:#475569;font-size:.62rem;">GPT-4o</span></span>
        <span style="color:#334155;">→</span>
        <span style="background:#0a1e35;border:1px solid #1d2e45;color:#22c55e;padding:4px 10px;border-radius:5px;font-size:.7rem;">💾 store_article<br><span style="color:#475569;font-size:.62rem;">ChromaDB</span></span>
        <span style="color:#334155;">→</span>
        <span style="background:#0a1e35;border:1px solid #22c55e;color:#22c55e;padding:4px 10px;border-radius:5px;font-size:.7rem;">🔔 send_notification<br><span style="color:#475569;font-size:.62rem;">Pushover → phone</span></span>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:5px 20px;font-size:.7rem;color:#64748b;line-height:1.6;">
        <div>• <span style="color:#94a3b8;">Claude</span> is the orchestrator — it calls all tools autonomously in the right order</div>
        <div>• <span style="color:#94a3b8;">DistilRoberta</span> runs locally with zero API cost for fast sentiment classification</div>
        <div>• <span style="color:#94a3b8;">ChromaDB</span> stores every article as embeddings — RAG context improves over time</div>
        <div>• <span style="color:#94a3b8;">Pushover</span> fires a phone alert for high-confidence negative signals or safeguard FAILs</div>
      </div>
    </div>
    """)

    
    with gr.Row():
        with gr.Column(scale=5):
            status_out = gr.HTML()
        with gr.Column(scale=1):
            run_now_btn = gr.Button("▶ Run Now", variant="primary")

    
    gr.HTML('<div class="section-label">📊 Session Stats</div>')
    stats_out = gr.HTML()

    
    gr.HTML('<div class="section-label">📰 Analysis Feed (newest first)</div>')
    results_out = gr.HTML()

    
    timer = gr.Timer(value=30)
    timer.tick(
        fn=load_dashboard,
        outputs=[status_out, stats_out, results_out],
    )

    
    demo.load(
        fn=load_dashboard,
        outputs=[status_out, stats_out, results_out],
    )

    
    run_now_btn.click(
        fn=manual_run,
        outputs=[status_out, stats_out, results_out],
    )


#entry point

if __name__ == "__main__":
    demo.launch(
        server_port=APP_CONFIG.server_port,
        share=APP_CONFIG.share,
    )
