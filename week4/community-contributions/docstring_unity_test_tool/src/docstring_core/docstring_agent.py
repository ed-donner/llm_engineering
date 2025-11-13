from src.docstring_core.docstring_models import DocstringOutputList
from src.docstring_core.docstring_prompts import SYSTEM_PROMPT_DOCSTRINGS, PROMPT_TEMPLATE_DOCSTRINGS
from src.core_base.agents.base_agents import BaseCodeGenerationAgent
from pathlib import Path

class DocstringAgent(BaseCodeGenerationAgent):
    """
    A specialized agent for generating docstrings from structured code inputs using a language model.
    
    This agent uses a specified model and prompt template for producing docstring outputs.
    
    Attributes:
      SYSTEM_PROMPT (str): The system prompt used to guide the output generation.
      PROMPT_TEMPLATE (str): The template for formatting the prompts sent to the model.
      OutputModel (Type): The model class defining the structure of the output generated.
    """
    SYSTEM_PROMPT = SYSTEM_PROMPT_DOCSTRINGS
    PROMPT_TEMPLATE = PROMPT_TEMPLATE_DOCSTRINGS
    OutputModel = DocstringOutputList

    def __init__(self, model_name: str, project_path: Path = None):
        """
        Initializes a DocstringAgent instance with a specified model name and an optional project path.
        
        Args:
          model_name (str): The name of the language model to be used for generation.
          project_path (Path, optional): The path to the project directory, defaults to None.
        """
        super().__init__(model_name=model_name, project_path=project_path)