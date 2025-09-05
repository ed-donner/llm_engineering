"""AI Mastered Dungeon Extraction Game main entrypoint module."""

from logging import getLogger

from .config import SCENE_PROMPT, SCENE_STYLE, START_SCENE, STORYTELLER_PROMPT
from .gameplay import Gameplay_Config, get_gameplay_function
from .illustrator import draw_dalle_2, draw_dalle_3, draw_gemini, draw_gpt, draw_grok
from .illustrator import draw_grok_x
from .interface import Interface_Config, get_interface
from .storyteller import narrate


# Choose draw function.
DRAW_FUNCTION = draw_dalle_2

# Configure the game.
game_config = Gameplay_Config(
    draw_func=DRAW_FUNCTION,
    narrate_func=narrate,
    scene_style=SCENE_STYLE,
    scene_prompt=SCENE_PROMPT,
    storyteller_prompt=STORYTELLER_PROMPT,
    error_img='images/machine.jpg',
    error_narrator='NEURAL SINAPSIS ERROR\n\n{ex}\n\nEND OF LINE\n\nRE-SUBMIT_',
    error_illustrator='NEURAL PROJECTION ERROR\n\n{ex}\n\nEND OF LINE\n\nRE-SUBMIT_',)

ui_config = Interface_Config(
    start_img='images/chair.jpg',
    place_img='images/machine.jpg',
    description_label='Cognitive Projection',
    title_label='The Neural Nexus',
    input_button='Imprint your will',
    input_label='Cognitive Imprint',
    input_command='Awaiting neural imprint…',
    start_scene=START_SCENE)


_logger = getLogger(__name__)

if __name__ == '__main__':
    _logger.info('STARTING GAME...')
    gameplay_function = get_gameplay_function(game_config)
    get_interface(gameplay_function, ui_config).launch(inbrowser=True, inline=False)
