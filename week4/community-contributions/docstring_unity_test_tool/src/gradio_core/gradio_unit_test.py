from src.unit_test_core.unit_test_executor import execute_unit_test_in_path


# ============================================================
#  Unit Test Generation Core
# ============================================================

async def gradio_generate_unit_tests(folder_path, model, names="", project_path=None):
    """
    Generates unit tests for Gradio components by executing test generation for each file in the specified folder.
    
    Args:
      folder_path (str): The path to the folder containing Gradio component files.
      model (str): The name of the model to use for test generation.
      names (str, optional): Comma-separated string of specific component names to generate tests for. Defaults to an empty string, which generates tests for all components.
      project_path (str, optional): The project root path required for test generation.
    
    Returns:
      str: A message indicating the result of the test generation process.
    """
    if not project_path:
        return "❌ Please provide the project root path (required)."

    target_names = [n.strip() for n in names.split(",")] if names else None

    await execute_unit_test_in_path(
        path=folder_path,
        model_name=model,
        target_names=target_names,
        project_path=project_path,
    )

    return "✅ Unit tests generated and written to 'tests/' folder."
