from loader import load_experiments
from runner import run_experiment
from writer import save_results

results = []

for experiment in load_experiments():
    print(f"Running experiment: {experiment.name}")

    result = run_experiment(experiment)
    results.append(result)

    print(f"Completed experiment: {experiment.name}")

save_results(results)
print(f"Saved results to results.json")