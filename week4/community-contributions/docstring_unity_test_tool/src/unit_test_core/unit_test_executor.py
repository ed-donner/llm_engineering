from typing import Optional, List
from src.core_base.executor.executor import execute_in_path
from src.unit_test_core.unit_test_generator import generate_unit_test_from_path_dict
from src.unit_test_core.unit_test_writer import UnitTestWriterWithReview

async def _unit_test_writer_wrapper(results: List[dict], project_path: str, **kwargs):
    """
    Wrapper function that manages the writing of unit tests using the UnitTestWriterWithReview class.
    
    Args:
      results (List[dict]): The list of generated unit test dictionaries.
      project_path (str): The path where the unit tests will be written.
      **kwargs: Additional keyword arguments that may include model_name.
    
    Returns:
      None
    """
    writer = UnitTestWriterWithReview(model_name=kwargs.get("model_name", "gpt-4o-mini"))
    await writer.write_unit_tests(results, project_path=project_path)

async def execute_unit_test_in_path(
    path: str,
    model_name: str = "gpt-4o-mini",
    project_path: str = "",
    target_names: Optional[List[str]] = None,
):
    """
    Executes unit test generation and writing in a specified path.
    
    This function first validates the project_path and then calls execute_in_path to handle the process of generating and writing unit tests.
    
    Args:
      path (str): The file or folder path for which to generate unit tests.
      model_name (str, optional): The model name to use for generation. Defaults to 'gpt-4o-mini'.
      project_path (str): The base path for the project, which cannot be empty.
      target_names (Optional[List[str]], optional): Specific names of targets to generate tests for.
    
    Raises:
      ValueError: If the project_path is not provided.
    
    Returns:
      None
    """
    if not project_path:
        raise ValueError("Debes proporcionar `project_path` para generar tests.")
    await execute_in_path(
        path=path,
        generate_func=generate_unit_test_from_path_dict,
        write_func=_unit_test_writer_wrapper,
        model_name=model_name,
        item_name="unit tests",
        target_names=target_names,
        project_path=project_path,
    )