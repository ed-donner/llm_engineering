"""AI Mastered Dungeon Extraction Game initialization module."""

from logging import basicConfig, getLogger

from dotenv import load_dotenv


# Environment initialization.
load_dotenv(override=True)

# Setup the global logger.
LOG_STYLE = '{'
LOG_LEVEL = 'INFO'
LOG_FORMAT = ('{asctime} {levelname:<8} {processName}({process}) '
              '{threadName} {name} {lineno} "{message}"')
basicConfig(level=LOG_LEVEL, style='{', format=LOG_FORMAT)

getLogger(__name__).info('INITIALIZED GAME LOGGER')
