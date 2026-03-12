"""
Gradio UI for the Indie Publisher / Funding Matcher.

Run from the indie-publisher-matcher directory:
  uv run python app.py
  or
  python app.py
"""
import gradio as gr
from publisher_framework import PublisherMatcherFramework
from publisher_models import ScoredOpportunity


def table_rows(memory: list[ScoredOpportunity]) -> list[list]:
    """Build table rows: Name, Description (short), Deadline, Fit Score, URL."""
    rows = []
    for s in memory:
        o = s.opportunity
        desc = (o.description[:80] + "...") if len(o.description) > 80 else o.description
        rows.append([o.name, desc, o.deadline, f"{s.fit_score:.0f}", o.url])
    return rows


def main():
    framework = PublisherMatcherFramework()
    framework.init_agents_as_needed()

    with gr.Blocks(title="Indie Publisher / Funding Matcher", fill_width=True) as ui:
        opportunities_state = gr.State(framework.memory)

        gr.Markdown(
            '<div style="text-align: center; font-size: 24px;">'
            "Indie Publisher & Funding Opportunity Matcher"
            "</div>"
        )
        gr.Markdown(
            "**Why this matters:** You're busy shipping. This tool keeps a list of publisher/funding "
            "opportunities (ID@Xbox, Epic MegaGrants, Indie Fund, etc.), scores each one 0–100 for "
            "indie fit (solo/small team, 6–18 months, PC/console), and surfaces the best matches so "
            "you can act instead of manually tracking who's open and whether you qualify."
        )
        gr.Markdown(
            "**How to use:** Click **Run scan & score** to load opportunities, score them, and add the "
            "best new one to the table. Use the **Fit** column to see the best matches; click a row to "
            "re-send a push alert (if Pushover is set). Run a scan weekly or when you're ready to pitch."
        )

        gr.Markdown(
            "**What Fit means:** 0–100 = how well the opportunity fits a typical indie (solo/small team, 6–18 mo, PC/console). "
            "Higher = stronger match. **50** = mid fit or we couldn't score it (fallback); treat as \"check yourself.\" "
            "Alerts fire when Fit ≥ 60 (configurable)."
        )
        gr.Markdown("---")
        run_status = gr.Markdown(value="*After you run a scan, the result will appear here.*", visible=True)
        gr.Markdown("**Opportunities surfaced so far:**")
        opportunities_dataframe = gr.Dataframe(
            headers=["Name", "Description", "Deadline", "Fit", "URL"],
            wrap=True,
            column_widths=[2, 4, 1, 1, 2],
            row_count=15,
            col_count=5,
            max_height=450,
        )

        def on_load(opps):
            status = "*After you run a scan, the result will appear here.*" if not opps else f"*Table has {len(opps)} opportunity/opportunities. Click Run to add more (if any are left).*"
            return table_rows(opps), opps, status

        def on_run(opps):
            framework.memory = opps
            memory, status = framework.run()
            return table_rows(memory), memory, status

        def on_reset():
            PublisherMatcherFramework.reset_memory()
            framework.memory = []
            return table_rows([]), [], "**Memory cleared.** Click **Run scan & score** to score opportunities from scratch (you’ll see new rows and possibly different Fit scores)."

        def on_select(opps, evt: gr.SelectData):
            if not opps or evt.index[0] >= len(opps):
                return
            scored = opps[evt.index[0]]
            framework.planner.messenger.alert(scored)

        ui.load(
            fn=on_load,
            inputs=[opportunities_state],
            outputs=[opportunities_dataframe, opportunities_state, run_status],
        )
        run_btn = gr.Button("Run scan & score", variant="primary")
        run_btn.click(
            fn=on_run,
            inputs=[opportunities_state],
            outputs=[opportunities_dataframe, opportunities_state, run_status],
        )
        reset_btn = gr.Button("Reset memory", variant="secondary")
        reset_btn.click(
            fn=on_reset,
            outputs=[opportunities_dataframe, opportunities_state, run_status],
        )
        opportunities_dataframe.select(fn=on_select, inputs=[opportunities_state], outputs=[])

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()
