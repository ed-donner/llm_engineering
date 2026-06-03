import gradio as gr
import requests
import json
from json_handlers import SettingsHandler, LanguagesHandler
from ollama_utils import get_ollama_response


class GradioUI:
    def __init__(self, models: list, settings: SettingsHandler, languages: LanguagesHandler):
        self.models = models
        self.settings = settings
        self.languages = languages

        self.langs = self.languages.get_supported_languages()

    def _translate_callback(self, text, model, translte_from, translte_to):
        model_options = self.settings.get_advanced_settings()

        full_response = ""
        chunck_response = get_ollama_response(model, text, translte_from, translte_to, model_options)
        for chunck in chunck_response:
            full_response += chunck
            yield full_response

    def _temp_setting_callback(self, temp_dropdown_val):
        self.settings.update_advanced_settings_param("temperature", temp_dropdown_val)

    def _top_k_setting_callback(self, top_k_dropdown_val):
        self.settings.update_advanced_settings_param("top_k", top_k_dropdown_val)

    def _top_p_setting_callback(self, top_p_dropdown_val):
        self.settings.update_advanced_settings_param("top_p", top_p_dropdown_val)

    def _reset_to_default_callback(self):
        temperature = 0.0
        top_k = 40.0
        top_p = 0.9
        default_settings = {
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p
        }
        self.settings.update_advanced_settings(default_settings)
        return temperature, top_k, top_p

    def build_and_launch(self):
        with gr.Blocks() as gui:
            gr.Markdown("# LLM Translator")
            with gr.Tab("Translate"):
                with gr.Row():
                    model_dropdown = gr.Dropdown(
                        label="Model",
                        info="Choose LLM Model",
                        choices=self.models
                    )
                with gr.Group():
                    with gr.Row():
                        translte_from = gr.Dropdown(
                            value=self.langs[0],
                            show_label=False,
                            choices=self.langs,
                            interactive=True
                        )
                        translte_to = gr.Dropdown(
                            value=self.langs[1],
                            show_label=False,
                            choices=self.langs,
                            interactive=True
                        )
                    with gr.Row():
                        translate_input = gr.Textbox(label="Your Input", lines=15, max_lines=15)
                        translate_output = gr.Textbox(label="Translated", lines=15, max_lines=15)
                    
                btn = gr.Button("Translate", variant="primary")
                btn.click(
                    fn=self._translate_callback,
                    inputs=[translate_input, model_dropdown, translte_from, translte_to],
                    outputs=translate_output
                )

            with gr.Tab("Advanced Settings"):
                temp_dropdown = gr.Number(
                    value=self.settings.get_advanced_setting_param("temperature"),
                    label="Temperature",
                    info="This parameter control how creative the model is\n0 means no creativity\n1 means very creative",
                    minimum=0,
                    maximum=1,
                    step=0.1,
                    interactive=True
                )

                gr.Markdown()  # Used only for spacing

                top_k_dropdown = gr.Number(
                    value=self.settings.get_advanced_setting_param("top_k"),
                    label="Top K",
                    info="A higher value (e.g. 100) will give more diverse answers\nwhile a lower value (e.g. 10) will be more conservative.",
                    minimum=1,
                    maximum=200,
                    step=1,
                    interactive=True
                )

                gr.Markdown()  # Used only for spacing

                top_p_dropdown = gr.Number(
                    value=self.settings.get_advanced_setting_param("top_p"),
                    label="Top P",
                    info="A higher value (e.g., 0.95) will lead to more diverse answers\nwhile a lower value (e.g., 0.5) will be more conservative",
                    minimum=0.1,
                    maximum=1.0,
                    step=0.1,
                    interactive=True
                )

                gr.Markdown()  # Used only for spacing

                reset_btn = gr.Button("Reset to Default")
                reset_btn.click(
                    fn=self._reset_to_default_callback,
                    outputs=[temp_dropdown, top_k_dropdown, top_p_dropdown]
                )

                temp_dropdown.change(self._temp_setting_callback, temp_dropdown)
                top_k_dropdown.change(self._top_k_setting_callback, top_k_dropdown)
                top_p_dropdown.change(self._top_p_setting_callback, top_p_dropdown)

        gui.launch()

