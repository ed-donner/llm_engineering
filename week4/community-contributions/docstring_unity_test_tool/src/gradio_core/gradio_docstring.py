from pathlib import Path
from src.docstring_core.docstring_generator import generate_docstring_from_path_dict
from src.docstring_core.docstring_writer import write_docstrings

# ============================================================
# Docstring Generation Core
# ============================================================

async def gradio_scan_and_generate(folder_path, model, names="", project_path=None):
    """
    Scan a folder and generate docstrings for the files found within.
    
    Args:
      folder_path (str): The path to the folder to scan for items.
      model (str): The model name to use for generating docstrings.
      names (str, optional): Comma-separated string of names to filter generated docstrings. Defaults to an empty string.
      project_path (str, optional): The path to the project directory. If None, defaults to the current path.
    
    Returns:
      tuple: A tuple containing the original docstring, generated docstring, source path, index, results list, and a status message.
    """
    target_names = [n.strip() for n in names.split(",")] if names else None

    results: list[dict] = await generate_docstring_from_path_dict(
        folder_path,
        model_name=model,
        target_names=target_names,
        project_path=project_path,
    )

    if not results:
        return "", "", "", 0, [], "❌ No items to process."

    results = [r for r in results if r["docstring"].strip()]
    if not results:
        return "", "", "", 0, [], "❌ No docstrings generated."

    first_item = results[0]
    return (
        first_item.get("original_docstring", ""),
        first_item["docstring"],
        first_item["source"],
        0,
        results,
        f"Item 1/{len(results)}",
    )

async def async_write_docstrings(file_path: Path, items: list[dict]):
    """
    Asynchronous wrapper for the function that writes multiple docstrings to a Python file.
    
    Args:
      file_path (Path): The path to the Python file where docstrings should be written.
      items (list[dict]): A list of dictionaries where each dictionary contains a name and a docstring for the items to update.
    
    Returns:
      None
    """
    await write_docstrings(file_path, items)

async def next_item(action: str, edited_text: str, results: list[dict], index: int):
    """
    Handle Accept or Skip actions and navigate to the next item in the results list.
    
    Args:
      action (str): The action to take, either 'Accept' or 'Skip'.
      edited_text (str): The edited text for the current item, unused in this function.
      results (list[dict]): A list of dictionaries containing items with their respective data.
      index (int): The current index of the item in the results to process.
    
    Returns:
      tuple: A tuple containing the original docstring, the processed docstring, the full source code, the updated index, results list, and a status message.
    """
    if not results or index >= len(results):
        return "", "", "", index, results, "❌ No items to process."

    if action == "Accept":
        item = results[index]
        await async_write_docstrings(Path(item["file_path"]), [item])

    next_index = index + 1
    if next_index >= len(results):
        return "", "", "", next_index, results, "✅ All items processed!"

    next_item_data = results[next_index]
    source_code = next_item_data.get("source")
    if source_code is None:
        with open(next_item_data["file_path"], "r", encoding="utf-8") as f:
            source_code = f.read()

    full_source = f"# Path: {next_item_data['file_path']}\n{source_code}"
    return (
        next_item_data.get("original_docstring", ""),
        next_item_data["docstring"],
        full_source,
        next_index,
        results,
        f"Item {next_index + 1}/{len(results)}",
    )

async def accept_all(_, results: list[dict], index: int):
    """
    Accept all remaining docstrings in the results list starting from the current index.
    
    Args:
      _ (str): An unused parameter.
      results (list[dict]): A list of dictionaries containing items with their respective data.
      index (int): The index from which to start accepting docstrings.
    
    Returns:
      tuple: A tuple containing an empty string, an empty string, an empty string, the count of accepted items, the updated results list, and a status message.
    """
    if not results or index >= len(results):
        return "", "", "", index, results, "❌ No items to process."

    for i in range(index, len(results)):
        item = results[i]
        await async_write_docstrings(Path(item["file_path"]), [item])

    return "", "", "", len(results), results, "✅ All items accepted!"