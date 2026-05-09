import logging


class AgentBase:
    """Base for ARIA agents. Uses a named logger so UI can map to agent and color."""
    name: str = "Agent"
    logger_name: str = "aria.agent"

    def __init__(self):
        self._logger = logging.getLogger(self.logger_name)

    def log(self, message: str) -> None:
        self._logger.info(message)
