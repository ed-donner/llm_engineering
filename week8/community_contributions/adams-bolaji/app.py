"""
Gradio UI for the Real Estate Comps Agent.
Usage: uv run python community_contributions/adams-bolaji/app.py
"""
import sys
from pathlib import Path

WEEK8 = Path(__file__).resolve().parent.parent.parent
ADAMS = Path(__file__).resolve().parent
if str(WEEK8) not in sys.path:
    sys.path.insert(0, str(WEEK8))
if str(ADAMS) not in sys.path:
    sys.path.insert(0, str(ADAMS))


def main():
    import gradio as gr
    from real_estate_comps_framework import RealEstateCompsFramework
    from models import PropertyOpportunity

    framework = RealEstateCompsFramework()
    framework.init_agents_as_needed()

    def get_table(opps):
        if not opps:
            return []
        return [
            [
                o.listing.product_description[:80] + "..." if len(o.listing.product_description) > 80 else o.listing.product_description,
                o.listing.price,
                o.estimate,
                o.discount,
                o.listing.url,
            ]
            for o in opps
        ]

    def run_scan():
        result = framework.run()
        return get_table(result)

    with gr.Blocks(title="Real Estate Comps Agent", fill_width=True) as ui:
        gr.Markdown("# Real Estate Comps Agent - Adams Bolaji")
        gr.Markdown(
            "RAG-based deal finder: scans listings, estimates value using comparable sales, "
            "alerts when a property is priced below fair market value."
        )
        opportunities = gr.State(framework.memory)
        df = gr.Dataframe(
            headers=["Description", "List Price", "Estimate", "Discount", "URL"],
            wrap=True,
            column_widths=[4, 1, 1, 1, 2],
            row_count=10,
            col_count=5,
            max_height=400,
        )
        ui.load(lambda: get_table(framework.memory), outputs=[df])
        btn = gr.Button("Run Scan")
        btn.click(run_scan, outputs=[df])

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()
