"""AI Mastered Dungeon Extraction Game Gradio interface module."""

from typing import NamedTuple

import gradio as gr
from logging import getLogger


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
    game_over_field: str
    game_over_label: str
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
            type="pil", show_label=False)
        # Scene's description.
        description_box = gr.Textbox(
            label=config.description_label, value=config.start_scene,
            interactive=False, show_copy_button=True)
        # Player's command.
        user_input = gr.Textbox(
            label=config.input_label, placeholder=config.input_command)
        # Submit button.
        submit_btn = gr.Button(config.input_button)

        # Define Game Over control.

        def _reset_game():
            """Return Initial values for game restart."""
            return (config.start_img, config.start_scene, [], '',
                    gr.update(interactive=True),
                    gr.update(value=config.input_button))

        def _game_over(scene, response):
            """Return Game Over values, blocking input field."""
            return (scene, response, [], config.game_over_field,
                    gr.update(interactive=False),
                    gr.update(value=config.game_over_label))

        def game_over_wrap(message, history, button_label):
            """Check Game over status Before and After Storyteller call."""
            # Check game over before.
            print(button_label)
            print(config.game_over_label)
            if button_label == config.game_over_label:
                _logger.warning('GAME OVER STATUS. RESTARTING...')
                return _reset_game()
            # Call Storyteller.
            scene, response, history, input = submit_function(message, history)
            _logger.warning(response)
            # Check game over after.
            if response.game_over:
                _logger.info('GAME OVER AFTER MOVE. LOCKING.')
                return _game_over(scene, response)
            # Return Storyteller response.
            return scene, response, history, input, gr.update(), gr.update()

        # Assign function to button click event.
        submit_btn.click(
            fn=game_over_wrap,
            inputs=[user_input, history_state, submit_btn],
            outputs=[scene_image, description_box, history_state, user_input,
                     user_input, submit_btn])
        # Assign function to input submit event. (Press enter)
        user_input.submit(
            fn=game_over_wrap,
            inputs=[user_input, history_state, submit_btn],
            outputs=[scene_image, description_box, history_state, user_input,
                     user_input, submit_btn])

    return ui


_logger = getLogger(__name__)
