# prompt_cost_calculator.py

import os
import gradio as gr
import tiktoken
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv(override=True)

# ── Model Pricing Table (USD per 1M tokens) ──────────────────────────────────

@dataclass
class Model:
    name: str
    provider: str
    input_cost: float    # per 1M tokens
    output_cost: float   # per 1M tokens
    speed: str
    quality: str
    context_k: int       # context window in K tokens

MODELS = [
    Model("GPT-4o",            "OpenAI",     2.50,  10.00, "Fast",      "Excellent", 128),
    Model("GPT-4o mini",       "OpenAI",     0.15,   0.60, "Very Fast", "Good",      128),
    Model("GPT-4.1",           "OpenAI",     2.00,   8.00, "Fast",      "Excellent", 1000),
    Model("Claude Sonnet 4.5", "Anthropic",  3.00,  15.00, "Fast",      "Excellent", 200),
    Model("Claude Haiku 3.5",  "Anthropic",  0.80,   4.00, "Very Fast", "Good",      200),
    Model("Claude Opus 4",     "Anthropic", 15.00,  75.00, "Medium",    "Best",      200),
    Model("Gemini 2.5 Pro",    "Google",     1.25,   5.00, "Fast",      "Excellent", 1000),
    Model("Gemini 2.0 Flash",  "Google",     0.075,  0.30, "Fastest",   "Good",      1000),
    Model("Grok-3",            "xAI",        3.00,  15.00, "Fast",      "Excellent", 131),
    Model("Deepseek-V3",       "Deepseek",   0.27,   1.10, "Fast",      "Very Good", 128),
    Model("Llama 3.3 70B",     "Meta/Groq",  0.59,   0.79, "Very Fast", "Good",       128),
    Model("Qwen3-235B",        "Alibaba",    0.22,   0.88, "Medium",    "Very Good", 128),
]

OUTPUT_RATIOS = {
    "Short (~0.5x)":  0.5,
    "Medium (~1.5x)": 1.5,
    "Long (~3x)":     3.0,
    "Code (~2x)":     2.0,
}

# ── Token counting ────────────────────────────────────────────────────────────

def count_tokens(text: str) -> int:
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)

# ── Core calculation ──────────────────────────────────────────────────────────

def calculate(prompt: str, output_mode: str, scale: int, provider_filter: str):
    if not prompt.strip():
        return (
            "### Paste a prompt above to see cost estimates.",
            [],
            "No data yet."
        )

    input_tokens  = count_tokens(prompt)
    ratio         = OUTPUT_RATIOS.get(output_mode, 1.5)
    output_tokens = int(input_tokens * ratio)
    total_tokens  = input_tokens + output_tokens

    # Filter models
    filtered = MODELS if provider_filter == "All" else [m for m in MODELS if m.provider == provider_filter]

    rows = []
    for m in filtered:
        input_cost  = (input_tokens  / 1_000_000) * m.input_cost  * scale
        output_cost = (output_tokens / 1_000_000) * m.output_cost * scale
        total_cost  = input_cost + output_cost

        def fmt(c):
            if c < 0.000001: return "$0.000000"
            if c < 0.01:     return f"${c:.6f}"
            if c < 1:        return f"${c:.4f}"
            return f"${c:.2f}"

        rows.append({
            "model":    m,
            "in_cost":  input_cost,
            "out_cost": output_cost,
            "total":    total_cost,
            "fmt_in":   fmt(input_cost),
            "fmt_out":  fmt(output_cost),
            "fmt_tot":  fmt(total_cost),
        })

    rows.sort(key=lambda r: r["total"])

    # Table for Gradio Dataframe
    table = []
    for i, r in enumerate(rows):
        rank = "🥇" if i == 0 else ("🥈" if i == 1 else ("🥉" if i == 2 else "  "))
        table.append([
            f"{rank} {r['model'].name}",
            r['model'].provider,
            r['model'].speed,
            r['model'].quality,
            f"${r['model'].input_cost:.3f}",
            f"${r['model'].output_cost:.3f}",
            r['fmt_in'],
            r['fmt_out'],
            r['fmt_tot'],
        ])

    headers = ["Model", "Provider", "Speed", "Quality",
               "In $/1M", "Out $/1M",
               f"Input Cost ({scale}x)", f"Output Cost ({scale}x)", f"Total ({scale}x)"]

    # Summary markdown
    cheapest  = rows[0]
    priciest  = rows[-1]
    savings   = (1 - cheapest["total"] / priciest["total"]) * 100 if priciest["total"] > 0 else 0

    if input_tokens < 500:
        rec = "**Gemini 2.0 Flash** or **GPT-4o mini** — short prompt, cheap/fast models dominate"
    elif input_tokens > 10_000:
        rec = "**Claude Sonnet 4.5** or **Gemini 2.5 Pro** — long context, pick high-window models"
    else:
        rec = "**Deepseek-V3** or **Qwen3-235B** — best quality/cost ratio for mid-length prompts"

    summary = f"""
## 📐 Token Analysis
| Metric | Value |
|---|---|
| Input tokens | **{input_tokens:,}** |
| Est. output tokens | **{output_tokens:,}** ({output_mode}) |
| Total tokens | **{total_tokens:,}** |
| Characters | **{len(prompt):,}** |
| Monthly scale | **{scale:,}× calls** |

## 💡 Recommendation
→ {rec}

## 💰 Cost Range
| | Model | Cost |
|---|---|---|
| 🟢 Cheapest | {cheapest['model'].name} | **{cheapest['fmt_tot']}** |
| 🔴 Priciest | {priciest['model'].name} | **{priciest['fmt_tot']}** |

> 💡 Switching from **{priciest['model'].name}** → **{cheapest['model'].name}** saves **{savings:.0f}%**
"""

    # Bar chart data string (simple ASCII for now, or use plot)
    chart_md = "### 📊 Cost Breakdown\n"
    max_total = rows[-1]["total"] if rows[-1]["total"] > 0 else 1
    for r in rows:
        bar_len = int((r["total"] / max_total) * 40) if max_total > 0 else 0
        bar = "█" * max(1, bar_len)
        chart_md += f"`{r['model'].name:<22}` {bar} {r['fmt_tot']}\n"

    return summary.strip(), [headers] + table, chart_md

# ── Gradio UI ─────────────────────────────────────────────────────────────────

providers = ["All"] + sorted(set(m.provider for m in MODELS))

CSS = """
body, .gradio-container { font-family: 'IBM Plex Mono', 'Courier New', monospace !important; }
h2, h3 { color: #00ff88 !important; }
footer { display: none !important; }
.gr-button-primary { background: #00ff88 !important; color: #000 !important; font-weight: 700 !important; }
"""

with gr.Blocks(css=CSS, theme=gr.themes.Monochrome(), title="Prompt Cost Calculator") as ui:

    gr.Markdown("# ⬡ Prompt Cost Calculator\nEstimate and compare LLM costs *before* you send a single token.")

    with gr.Row():
        with gr.Column(scale=5):
            prompt_box = gr.Textbox(
                label="📝 Your Prompt",
                placeholder="Paste your prompt here...",
                lines=12,
            )
        with gr.Column(scale=3):
            output_mode   = gr.Radio(label="Expected Output Length", choices=list(OUTPUT_RATIOS.keys()), value="Medium (~1.5x)")
            scale_slider  = gr.Slider(label="Monthly API Calls (scale)", minimum=1, maximum=100_000, step=100, value=1)
            provider_drop = gr.Dropdown(label="Filter by Provider", choices=providers, value="All")
            calc_btn      = gr.Button("⚡ Calculate Costs", variant="primary")

    with gr.Row():
        summary_md = gr.Markdown(value="*Paste a prompt and click Calculate.*")

    with gr.Row():
        chart_md = gr.Markdown()

    cost_table = gr.Dataframe(
        label="📋 Full Cost Breakdown (sorted cheapest → priciest)",
        interactive=False,
        wrap=True,
    )

    gr.Markdown("*Token count via `tiktoken` cl100k_base. Pricing current as of 2025 — always verify with provider docs before production use.*")

    # Wire up events
    inputs  = [prompt_box, output_mode, scale_slider, provider_drop]
    outputs = [summary_md, cost_table, chart_md]

    calc_btn.click(fn=calculate, inputs=inputs, outputs=outputs)

    # Live recalc on any change
    for component in [prompt_box, output_mode, scale_slider, provider_drop]:
        component.change(fn=calculate, inputs=inputs, outputs=outputs)

ui.launch(inbrowser=True)