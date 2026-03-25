class BaseAgent:
    """Shared base class for all triage agents — logging with colour."""

    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    BLUE   = "\033[94m"
    RESET  = "\033[0m"
    color  = RESET

    def log(self, message: str) -> None:
        print(f"{self.color}[{self.__class__.__name__}] {message}{self.RESET}")
