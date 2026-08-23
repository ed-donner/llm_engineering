"""
Investment Research UI - minimal Gradio interface.
Run: cd haastrupea && python price_is_right.py
"""

import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

import gradio as gr
from research_framework import ResearchFramework


def table_for(opps):
    return [
        [opp.ticker, opp.recommendation, f"{opp.confidence:.0%}", opp.summary[:100] + "..." if len(opp.summary) > 100 else opp.summary, opp.url]
        for opp in opps
    ]


def run_research():
    fw = ResearchFramework()
    fw.init_agents_as_needed()
    fw.run()
    return table_for(fw.memory)


with gr.Blocks(title="Investment Research") as ui:
    gr.Markdown("## Investment Research - Scanner → RAG → Recommendation")
    df = gr.Dataframe(
        headers=["Ticker", "Recommendation", "Confidence", "Summary", "URL"],
        value=[],
        interactive=False,
    )
    run_btn = gr.Button("Run Research", variant="primary")
    run_btn.click(run_research, outputs=df)

ui.launch()
