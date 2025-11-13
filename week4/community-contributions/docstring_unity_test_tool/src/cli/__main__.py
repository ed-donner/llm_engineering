import typer
from src.cli.docstring_cli import docstring_app
from src.cli.unit_test_cli import unit_test_app   

app = typer.Typer(help="LLM-based developer tools CLI")

# Register subcommands
app.add_typer(docstring_app, name="docstring")
app.add_typer(unit_test_app, name="unit_test")  

if __name__ == "__main__":
    app()
    