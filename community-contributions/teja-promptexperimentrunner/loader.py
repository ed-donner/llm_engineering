import json

from models import PromptExperiment

def load_experiments(path="experiments.json"):
    with open(path, "r") as f:
        experiments = json.load(f)

    for exp in experiments:
        yield PromptExperiment(
            name=exp["name"],
            task_type=exp["task_type"],
            system_prompt=exp["system_prompt"],
            user_input=exp["user_input"],
        )
