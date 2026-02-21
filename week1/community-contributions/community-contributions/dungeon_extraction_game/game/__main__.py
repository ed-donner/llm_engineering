"""AI Mastered Dungeon Extraction Game main entrypoint module."""

from logging import getLogger

from .config import GAME_CONFIG, UI_CONFIG
from .gameplay import get_gameplay_function
from .interface import get_interface


_logger = getLogger(__name__)

if __name__ == '__main__':
    _logger.info('STARTING GAME...')
    gameplay_function = get_gameplay_function(GAME_CONFIG)
    get_interface(gameplay_function, UI_CONFIG).launch(inbrowser=True, inline=False)
