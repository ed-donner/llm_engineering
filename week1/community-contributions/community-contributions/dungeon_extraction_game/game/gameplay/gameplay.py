"""AI Mastered Dungeon Extraction Game gameplay module."""

from logging import getLogger
from typing import Callable, NamedTuple


# Define gameplay's configuration class.
class Gameplay_Config(NamedTuple):
    """Gradio interface configuration class."""
    draw_func: Callable
    narrate_func: Callable
    scene_style: str
    scene_prompt: str
    storyteller_prompt: str
    disable_img: str
    error_img: str
    error_narrator: str
    error_illustrator: str


# Define Game's functions.

def get_gameplay_function(config: Gameplay_Config):
    """Return a pre-configured turn gameplay function."""
    def gameplay_function(message, history):
        """Generate Game Master's response and draw the scene image."""
        # Request narration.
        _logger.info(f'NARRATING SCENE...')
        try:
            response = config.narrate_func(message, history, config.storyteller_prompt)
        except Exception as ex:
            scene = config.error_img
            response = config.error_narrator.format(ex=ex)
            _logger.error(f'ERROR NARRATING SCENE: {ex}\n{message}\n{history}')
            return scene, response, history, message
        # Update history.
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response.model_dump_json()})
        # Draw scene.
        if config.draw_func:
            _logger.info(f'DRAWING SCENE...')
            try:
                scene_data = {'scene_description': response.scene_description,
                              'scene_style': config.scene_style}
                scene_prompt = config.scene_prompt.format(**scene_data)
                _logger.info(f'PROMPT BODY IS: \n\n{scene_prompt}\n')
                _logger.info(f'PROMPT LENGTH IS: {len(scene_prompt)}')
                scene = config.draw_func(scene_prompt)
            except Exception as ex:
                scene = config.error_img
                response = config.error_illustrator.format(ex=ex)
                _logger.warning(f'ERROR DRAWING SCENE: {ex}')
                return scene, response, history, ''
        else:
            _logger.info(f'DRAWING DISABLED...')
            scene = config.disable_img
        return scene, response, history, ''
    return gameplay_function


_logger = getLogger(__name__)
