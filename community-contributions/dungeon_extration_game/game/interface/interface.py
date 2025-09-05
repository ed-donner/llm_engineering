"""AI Mastered Dungeon Extraction Game Gradio interface module."""

from typing import NamedTuple

import gradio as gr


# Define interface's configuration class.
class Interface_Config(NamedTuple):
    """Gradio interface configuration class."""
    start_img: str
    place_img: str
    description_label: str
    title_label: str
    input_button: str
    input_label: str
    input_command: str
    start_scene: str


# Define game's interface.
def get_interface(submit_function, config: Interface_Config):
    """Create a game interface service."""
    with gr.Blocks(title=config.title_label) as ui:
        # Title.
        gr.Markdown(config.title_label)
        # Hidden state for history.
        history_state = gr.State([])
        # Scene's image.
        scene_image = gr.Image(
            label="Scene", value=config.start_img, placeholder=config.place_img,
            type="pil", show_label=False, show_copy_button=True)
        # Scene's description.
        description_box = gr.Textbox(
            label=config.description_label, value=config.start_scene,
            interactive=False, show_copy_button=True)
        # Player's command.
        user_input = gr.Textbox(
            label=config.input_label, placeholder=config.input_command)
        user_input.submit(
            fn=submit_function,
            inputs=[user_input, history_state],
            outputs=[scene_image, description_box, history_state, user_input])
        # Submit button.
        submit_btn = gr.Button(config.input_button)
        submit_btn.click(
            fn=submit_function,
            inputs=[user_input, history_state],
            outputs=[scene_image, description_box, history_state, user_input])
    return ui
