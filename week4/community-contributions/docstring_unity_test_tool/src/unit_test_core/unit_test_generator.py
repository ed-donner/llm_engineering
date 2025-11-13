from typing import List, Optional
from pathlib import Path
from src.core_base.generate.generator_manager import BaseGenerationManager
from src.unit_test_core.unit_test_agent import UnitTestAgent


class UnitTestGenerationManager(BaseGenerationManager):
    """
    Manager for generating unit tests from files or folders using a UnitTestAgent.
    
    This manager requires a project_path to mirror the structure of the source code inside the /tests directory.
    
    Attributes:
      agent_class (Type[UnitTestAgent]): The agent used for generating unit tests.
    """

    agent_class = UnitTestAgent

    def __init__(self, model_name: str = "gpt-4o-mini", project_path: Path = None):
        """
        Initializes the UnitTestGenerationManager with the specified model and project path.
        
        Args:
            model_name (str): The model to be used for code generation.
            project_path (Path): The root path of the project to index and mirror.
        
        Raises:
            ValueError: If project_path is None, a ValueError is raised.
        """
        if project_path is None:
            raise ValueError("❌ 'project_path' is required for UnitTestGenerationManager.")
        super().__init__(model_name=model_name, project_path=project_path)



async def generate_unit_test_from_path_dict(
    path: str,
    model_name: str = "gpt-4o-mini",
    target_names: Optional[List[str]] = None,
    project_path: Optional[str] = None
) -> List[dict]:
    """
    Generates unit tests from a specified file or folder path.
    
    This function requires a valid project_path to correctly mirror the directory structure in the /tests directory.
    
    Args:
      path (str): The path to the file or folder from which to generate unit tests.
      model_name (str, optional): The name of the model to use for generation. Defaults to 'gpt-4o-mini'.
      target_names (Optional[List[str]], optional): A list of specific target names to generate tests for. Defaults to None.
      project_path (Optional[str], optional): The root path of the project to index and mirror. Defaults to None.
    
    Returns:
      List[dict]: A list of generated unit test definitions.
    """
    if not project_path:
        raise ValueError("[ERROR] 'project_path' is required to generate mirrored test files.")

    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"[ERROR] Path not found: {path}")

    project_path_obj = Path(project_path)
    manager = UnitTestGenerationManager(model_name=model_name, project_path=project_path_obj)
    results = await manager.generate_for_path(path, target_names=target_names)
    return results