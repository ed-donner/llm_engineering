
import gradio as gr

from .Game import Game

class Gui:
    def __init__(self, game: Game):
        self.lang = None
        self.turns_input_msb = None
        self.expenses_output_mrk = None
        self.talks_output_mrk = None
        self.run_btn = None
        self.game = game

    def gui(self):
        with gr.Blocks() as blck:
            with gr.Row():
                with gr.Column(scale=1):
                    self.lang = gr.Dropdown(
                        label="Select chat lang.:",
                        choices=(("English","English"),("Czech","Czech")),
                        value="English",
                        interactive=True
                    )
                    self.turns_input_msb = gr.Number(16, label="Count of turns:")
                    self.expenses_output_mrk = gr.Json(label="Costs of Heroic talks:")
                with gr.Column(scale=3):
                    self.talks_output_mrk = gr.Markdown("Pre-cave's Heroic talks:")
            with gr.Row():
                self.run_btn = gr.Button("Let's talk!")
                self.run_btn.click(
                    fn=self.game.lets_talk,
                    inputs=[self.turns_input_msb, self.lang],
                    outputs=[self.expenses_output_mrk, self.talks_output_mrk]
                )
        return blck

    def run(self):
        self.gui().launch(inbrowser=True)
