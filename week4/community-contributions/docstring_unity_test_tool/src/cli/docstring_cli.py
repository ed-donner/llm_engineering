import typer
from src.docstring_core.docstring_executor import execute_docstring_in_path
from constants import models

docstring_app = typer.Typer(help="Python docstring auto-generator and updater")

@docstring_app.command("generate")
def scan_and_generate(
    path: str = typer.Argument(..., help="Path to file or folder to scan"),
    model_name: str = typer.Option(
        "gpt-4o-mini",
        "--model",
        "-m",
        help=f"Model to use ({', '.join(models)})",
        case_sensitive=False,
    ),
    names: str = typer.Option(
        None,
        "--names",
        "-n",
        help="Comma-separated list of function/class names to process (e.g. 'foo,bar,BazClass')",
    ),
    project_path: str = typer.Option(
        None,
        "--project",
        "-p",
        help="Root path of the project to index (optional)",
    ),
):
    """
    Automatically scans a specified folder or file to update docstrings using the selected model. This function can also filter the update process to specific functions or classes provided in the input.
    
    Args:
      path (str): The file or folder path to scan for docstrings.
      model_name (str): The name of the model to use for generating docstrings. Default is 'gpt-4o-mini'.
      names (str): A comma-separated list of function or class names to specifically process. This is optional.
      project_path (str): The root path of the project to index, which is also optional.
    
    Raises:
      Exit: If the provided model name is invalid.
    
    Returns:
      None: This function performs actions and does not return a value.
    """
    if model_name not in models:
        typer.echo(f"❌ Invalid model '{model_name}'. Available: {', '.join(models)}")
        raise typer.Exit(code=1)

    target_names = [n.strip() for n in names.split(",")] if names else None

    typer.echo(f"🔍 Scanning {path} using {model_name}...")
    if target_names:
        typer.echo(f"🎯 Filtering for: {', '.join(target_names)}")
    if project_path:
        typer.echo(f"🏷 Using project index at: {project_path}")

    execute_docstring_in_path(
        path=path,
        model_name=model_name,
        target_names=target_names,
        project_path=project_path,  # for project indexer
    )