import gradio as gr

from resource_agent_framework import ResourceScoutFramework


class App:
    def __init__(self):
        self.framework = ResourceScoutFramework()

    @staticmethod
    def _table(memory):
        return [
            [
                item.resource.title,
                item.resource.source,
                item.resource.url,
                f"{item.estimated_quality:.2f}",
                item.created_at,
            ]
            for item in memory
        ]

    def load_initial(self):
        return []

    def run_once(self, topic: str):
        latest_results = self.framework.run(topic=topic)
        return (
            self._table(latest_results),
            f"Completed autonomous scan for topic: {topic} (showing top {len(latest_results)} candidates from this run)",
        )

    def run(self):
        with gr.Blocks(title="Study Resource Scout", fill_width=True) as ui:
            gr.Markdown(
                "# Study Resource Scout\n"
                "Planner-driven multi-agent loop for discovering and alerting high-quality learning resources."
            )
            with gr.Row():
                topic = gr.Textbox(
                    label="Topic",
                    value="llm agents",
                    placeholder="e.g., llm evals, rag systems, agent safety",
                )
            with gr.Row():
                run_button = gr.Button("Find Top 5 Resources", variant="primary")
            table = gr.Dataframe(
                headers=["Title", "Source", "URL", "Score", "Timestamp"],
                interactive=False,
                wrap=True,
                col_count=(5, "fixed"),
            )
            status = gr.Textbox(label="Status", interactive=False)

            ui.load(self.load_initial, inputs=[], outputs=[table])
            run_button.click(self.run_once, inputs=[topic], outputs=[table, status])

        ui.launch(share=False, inbrowser=True)
