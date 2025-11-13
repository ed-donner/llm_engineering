from src.unit_test_core.unit_test_models import UnitTestOutputList
from src.unit_test_core.unit_test_prompts import SYSTEM_PROMPT_TESTS, PROMPT_TEMPLATE_TESTS
from src.core_base.agents.base_agents import BaseCodeGenerationAgent
from pathlib import Path

class UnitTestAgent(BaseCodeGenerationAgent):
    """
    A code generation agent for creating unit tests based on user-defined prompts and a specific model.
    
    Attributes:
      SYSTEM_PROMPT (str): The system prompt used for generating unit tests.
      PROMPT_TEMPLATE (str): The template used for generating prompts for unit tests.
      OutputModel (Type): The model representing the output of generated unit tests.
    """
    SYSTEM_PROMPT = SYSTEM_PROMPT_TESTS
    PROMPT_TEMPLATE = PROMPT_TEMPLATE_TESTS
    OutputModel = UnitTestOutputList

    def __init__(self, model_name: str, project_path: Path = None):
        """
        Initializes a UnitTestAgent instance.
        
        Args:
          model_name (str): The name of the model to be used for code generation.
          project_path (Path | None, optional): The path to the project where the generated tests will be stored. Defaults to None.
        """
        super().__init__(model_name=model_name, project_path=project_path)