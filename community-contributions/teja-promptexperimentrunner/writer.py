import json
from pathlib import Path
from models import ExperimentResult

def save_results(results: list[ExperimentResult], path: str = "results.json") -> None:
    output_path = Path(path)

    results_data = [result.model_dump() for result in results]
    with open(output_path, "w") as file:
        json.dump(results_data, file, indent=4)
