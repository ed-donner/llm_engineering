from pathlib import Path
from typing import Callable, List, Dict, Optional, Any

async def execute_in_path(
    path: str,
    generate_func: Callable[..., Any],
    write_func: Callable[..., Any],
    model_name: str = "gpt-4o-mini",
    project_path: Optional[str] = None,
    target_names: Optional[List[str]] = None,
    item_name: str = "items",
):
    """
    Asynchronously executes a function in the specified path and writes the results using another function.
    
    Args:
      path (str): The filesystem path where the operation will be executed.
      generate_func (Callable[..., Any]): A callable that generates results based on the execution context.
      write_func (Callable[..., Any]): A callable that writes the generated results to the specified location.
      model_name (str, optional): The name of the model to use for generation, defaults to 'gpt-4o-mini'.
      project_path (Optional[str], optional): An optional path to the project context.
      target_names (Optional[List[str]], optional): A list of target names to filter results, if any.
      item_name (str, optional): A label for the items being processed, defaults to 'items'.
    
    Returns:
      None: This function does not return any value, it performs actions directly.
    """
    path_obj = Path(path).resolve()
    if not path_obj.exists():
        print(f"[WARN] {path} not found.")
        return

    results = await generate_func(str(path_obj), model_name, target_names, project_path)
    if not results:
        print(f"[INFO] {item_name} not generated.")
        return

    grouped: Dict[str, List[dict]] = {}
    for item in results:
        grouped.setdefault(item["file_path"], []).append(item)

    # Detecta tipo de writer según su firma
    for file_path, items in grouped.items():
        try:
            await write_func(Path(file_path), items, model_name=model_name, project_path=project_path)
        except TypeError:
            # Caso: writer que agrupa internamente (como UnitTestWriterWithReview)
            await write_func(results, project_path=project_path, model_name=model_name)
            break  # Ya procesa todo de una vez
        print(f"✅ {item_name.capitalize()} writen in {file_path}")

    print(f"[OK] {item_name.capitalize()} successfuly actualized.")