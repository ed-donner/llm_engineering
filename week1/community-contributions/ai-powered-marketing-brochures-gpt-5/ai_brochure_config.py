import os
from dotenv import load_dotenv

class AIBrochureConfig:
    """
    Configuration class to load environment variables.
    """

    def __get_config_value(self, key: str):
        """
        Get the value of an environment variable.
        """
        if not key:
            raise ValueError("Key must be provided")

        value: str | None = os.getenv(key)
        if not value:
            raise ValueError(f"Environment variable '{key}' not found")

        return value

    def _get_str(self, key: str) -> str:
        """
        Get a string value from the environment variables.
        """
        return self.__get_config_value(key)

    def _get_int(self, key: str) -> int:
        """
        Get an integer value from the environment variables.
        """
        value = self.__get_config_value(key)
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Environment variable '{key}' must be an integer")

    @property
    def openai_api_key(self) -> str:
        """
        Get the OpenAI API key from the environment variables.
        """
        if self.__openai_api_key == "":
            self.__openai_api_key = self._get_str("OPENAI_API_KEY")
        return self.__openai_api_key

    @property
    def model_name(self) -> str:
        """
        Get the model name from the environment variables.
        """
        if self.__model_name == "":
            self.__model_name = self._get_str("MODEL_NAME")
        return self.__model_name

    def __init__(self) -> None:
        load_dotenv(dotenv_path=".env")
        self.__openai_api_key: str = ""
        self.__model_name: str = ""
