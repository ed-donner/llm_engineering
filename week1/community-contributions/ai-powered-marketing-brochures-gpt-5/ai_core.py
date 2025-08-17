import openai
from abc import ABC, abstractmethod
from ai_brochure_config import AIBrochureConfig
from typing import Any, cast, Generic, TypeVar
from openai.types.responses import ResponseInputItemParam, Response, ResponseOutputMessage

TAiResponse = TypeVar('TAiResponse', default=Any)

class HistoryManager:
    """
    Manage chat history and system behavior for a conversation with the model.
    """
    @property
    def chat_history(self) -> list[ResponseInputItemParam]:
        """
        Return the accumulated conversation as a list of response input items.
        """
        return self.__chat_history

    @property
    def system_behavior(self) -> str:
        """
        Return the system behavior (instructions) used for this conversation.
        """
        return self.__system_behavior

    def __init__(self, system_behavior: str) -> None:
        """
        Initialize the history manager.

        Parameters:
            system_behavior: The system instruction string for the conversation.
        """
        self.__chat_history: list[ResponseInputItemParam] = []
        self.__system_behavior: str = system_behavior

    def add_user_message(self, message: str) -> None:
        """
        Append a user message to the chat history.

        Parameters:
            message: The user text to add.
        """
        self.__chat_history.append({
            "role": "user",
            "content": [{"type": "input_text", "text": message}],
        })

    def add_assistant_message(self, output_message: Response) -> None:
        """
        Append the assistant's output to the chat history.

        Parameters:
            output_message: The model response to convert and store.
        """
        for out in output_message.output:
            # Convert the Pydantic output model to an input item shape
            self.__chat_history.append(
                cast(ResponseInputItemParam, out.model_dump(exclude_unset=True))
            )


class AICore(ABC, Generic[TAiResponse]):
    """
    Abstract base class for AI core functionalities.
    """
    @property
    def config(self) -> AIBrochureConfig:
        """
        Return the stored AIBrochureConfig for this instance.

        Returns:
            AIBrochureConfig: The current configuration used by this object.

        Notes:
            - This accessor returns the internal configuration reference. Mutating the returned
              object may affect the internal state of this instance.
            - To change the configuration, use the appropriate setter or factory method rather
              than modifying the returned value in-place.
        """
        return self.__config

    @config.setter
    def config(self, config: AIBrochureConfig | None) -> None:
        """
        Set the instance configuration for the AI brochure generator.

        Parameters
        ----------
        config : AIBrochureConfig | None
            The configuration to assign to the instance. If None, the instance's
            configuration will be reset to a newly created default AIBrochureConfig.

        Returns
        -------
        None

        Notes
        -----
        This method stores the provided configuration on a private attribute
        """
        if config is None:
            self.__config = AIBrochureConfig()
        else:
            self.__config = config

    @property
    def _ai_api(self) -> openai.OpenAI:
        """
        Return the cached OpenAI API client, initializing it on first access.

        This private helper lazily constructs and caches an openai.OpenAI client using
        the API key found on self.config.openai_api_key. On the first call, if the
        client has not yet been created, the method verifies that self.config is set,
        creates the client with openai.OpenAI(api_key=...), stores it on
        self.__ai_api, and returns it. Subsequent calls return the same cached
        instance.

        Returns:
            openai.OpenAI: A configured OpenAI API client.

        Raises:
            ValueError: If self.config is None when attempting to initialize the client.

        Notes:
            - The method mutates self.__ai_api as a side effect (caching).
            - The caller should treat this as a private implementation detail.
            - Thread safety is not guaranteed; concurrent initialization may result in
              multiple client instances if invoked from multiple threads simultaneously.
        """
        if self.__ai_api is None:
            if self.config is None:
                raise ValueError("Configuration must be set before accessing AI API")
            self.__ai_api = openai.OpenAI(api_key=self.config.openai_api_key)
        return self.__ai_api

    @property
    def history_manager(self) -> HistoryManager:
        """
        Return the history manager for this AI core instance.

        This property provides access to the HistoryManager that tracks the chat
        history and system behavior.

        Returns:
            HistoryManager: The current history manager. This property always returns
            a HistoryManager instance and never None.
        """
        return self.__history_manager

    def __init__(self, config: AIBrochureConfig, system_behavior: str) -> None:
        """
        Initializes the AI core with the provided configuration.

        Parameters:
            config (AIBrochureConfig): The configuration object for the AI core.
            system_behavior (str): The behavior of the system.
        """
        # Initialize all instance-level attributes here
        self.__config: AIBrochureConfig = config
        self.__history_manager: HistoryManager = HistoryManager(system_behavior)
        self.__ai_api: openai.OpenAI | None = None

        if __debug__:
            # Sanity check: confirm attributes are initialized
            assert hasattr(self, "_AICore__config")
            assert hasattr(self, "_AICore__history_manager")
            assert hasattr(self, "_AICore__ai_api")

    @abstractmethod
    def ask(self, question: str) -> TAiResponse:
        """
        Ask a question to the AI model.

        Parameters:
            question: The question to ask.

        Returns:
            TAiResponse: The model's response type defined by the subclass.
        """
        pass