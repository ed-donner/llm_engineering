# imports

import os
from dotenv import load_dotenv
from huggingface_hub import login
from datasets import load_dataset, Dataset, DatasetDict
import matplotlib.pyplot as plt
import json

# environment

load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'your-key-if-not-using-env')
os.environ['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY', 'your-key-if-not-using-env')
os.environ['HF_TOKEN'] = os.getenv('HF_TOKEN', 'your-key-if-not-using-env')

# Log in to HuggingFace

hf_token = os.environ['HF_TOKEN']
login(hf_token, add_to_git_credential=True)

# One more import - the Item class
# If you get an error that you need to agree to Meta's terms when you run this, then follow the link it provides you and follow their instructions
# You should get approved by Meta within minutes
# Any problems - message me or email me!

from items import Item

# Load in our dataset
# Open and read the JSON file
with open('/home/ivob/Projects/llm_engineering/project/data/training_data.json', 'r') as file:
    dataset = json.load(file)

# Print the data
print(dataset)

print(f"Number of Situations: {len(dataset):,}")

# Investigate a particular datapoint
datapoint = dataset[2]

# Investigate

print(datapoint["input"])
print(datapoint["result"])
print(datapoint["reason"])


# Plot the distribution of results

# Count the occurrences of "normal" and "anomalous" results
situation_counts = {"normal": 0, "anomalous": 0}
for entry in dataset:
    result = entry.get("result", "unknown").lower()
    if result in situation_counts:
        situation_counts[result] += 1

# Extract keys and values for the bar chart
labels = list(situation_counts.keys())
counts = list(situation_counts.values())

# Plot the bar chart
plt.figure(figsize=(8, 6))
plt.bar(labels, counts, color=['green', 'red'], alpha=0.7)

# Add labels and title
plt.xlabel("Situation Type", fontsize=12)
plt.ylabel("Count", fontsize=12)
plt.title("Number of Normal vs Anomalous Situations", fontsize=14)

# Annotate bars with counts
for i, count in enumerate(counts):
    plt.text(i, count + 0.2, str(count), ha='center', fontsize=10)

# Display the plot
plt.tight_layout()
plt.show()

# So what are the anomalous items??

for datapoint in dataset:
    try:
        result = datapoint["result"]
        if result == "anomalous":
            print(datapoint['input'])
    except ValueError as e:
        pass

# Create an Item object for each with a result

items = []
for datapoint in dataset:
    try:
        result = datapoint["result"]
        if result == 'normal' or result == 'anomalous':
            item = Item(datapoint, result)
            if item.include:
                items.append(item)
    except ValueError as e:
        pass

print(f"There are {len(items):,} items")
