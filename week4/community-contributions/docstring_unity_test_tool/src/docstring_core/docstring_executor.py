from pathlib import Path
import asyncio
from typing import Optional, List

from src.core_base.executor.executor import execute_in_path
from src.docstring_core.docstring_generator import generate_docstring_from_path_dict
from src.docstring_core.docstring_writer import write_docstrings

async def _docstring_writer_wrapper(file_path: Path, items: List[dict], **_):
    """
    Wrapper function to write docstrings asynchronously to a specified file.
    
    Args:
      file_path (Path): The path to the Python file where docstrings will be written.
      items (List[dict]): A list of dictionaries containing docstring information to be written.
    
    Returns:
      None
    """
    await write_docstrings(file_path, items)

def execute_docstring_in_path(
    path: str,
    model_name: str = "gpt-4o-mini",
    target_names: Optional[List[str]] = None,
    project_path: Optional[str] = None
):
    """
    Executes the generation and writing of docstrings in a specified path.
    
    This function runs an asynchronous process that generates docstrings using the specified model and writes them to the given path.
    
    Args:
      path (str): The path where docstrings should be generated and written.
      model_name (str, optional): The name of the model to use for generation. Defaults to 'gpt-4o-mini'.
      target_names (Optional[List[str]], optional): Specific targets for which docstrings should be generated. Defaults to None.
      project_path (Optional[str], optional): Optional path to the project. Defaults to None.
    
    Returns:
      None
    """
    asyncio.run(
        execute_in_path(
            path=path,
            generate_func=generate_docstring_from_path_dict,
            write_func=_docstring_writer_wrapper,
            model_name=model_name,
            item_name="docstrings",
            target_names=target_names,
            project_path=project_path
        )
    )