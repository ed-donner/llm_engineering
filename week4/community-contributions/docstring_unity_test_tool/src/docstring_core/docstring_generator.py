from typing import List, Optional
from pathlib import Path
from src.core_base.generate.generator_manager import BaseGenerationManager
from src.docstring_core.docstring_agent import DocstringAgent

class DocstringGenerationManager(BaseGenerationManager):
    """
    Manager for generating docstrings using the specified agent.
    
    This class extends the BaseGenerationManager and is responsible for setting up the agent used for docstring generation.
    
    Attributes:
      agent_class (Type[DocstringAgent]): The class of the agent used for generation.
    """
    agent_class = DocstringAgent

    def __init__(self, model_name: str = "gpt-4o-mini", project_path: Optional[Path] = None):
        """
        Initializes the DocstringGenerationManager with the specified model name and project path.
        
        Args:
          model_name (str): The name of the model to use, default is 'gpt-4o-mini'.
          project_path (Optional[Path]): The path to the project, if provided.
        """
        super().__init__(model_name=model_name, project_path=project_path)


# -----------------------------
# Wrapper function (CLI/Gradio)
# -----------------------------
async def generate_docstring_from_path_dict(
    path: str,
    model_name: str = "gpt-4o-mini",
    target_names: Optional[List[str]] = None,
    project_path: Optional[str] = None
) -> List[dict]:
    """
    Generates docstrings from a given path dictionary asynchronously.
    
    Args:
      path (str): The file path to generate docstrings for.
      model_name (str): The name of the model to use, default is 'gpt-4o-mini'.
      target_names (Optional[List[str]]): A list of target names for which docstrings should be generated.
      project_path (Optional[str]): An optional project path to use for the generation.
    
    Returns:
      List[dict]: A list of dictionaries containing the generated docstrings.
    """
    project_path_obj = Path(project_path) if project_path else None
    manager = DocstringGenerationManager(model_name=model_name, project_path=project_path_obj)
    return await manager.generate_for_path(path, target_names=target_names)