import json
import os
from pathlib import Path
from huggingface_hub import InferenceClient
from dotenv import load_dotenv


load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
HF_TOKEN = os.getenv("HF_TOKEN")

client = InferenceClient(
    model="Qwen/Qwen2.5-72B-Instruct",
    token=HF_TOKEN
)

DEFINITIONS = {
    "valid": "allocations satisfy demand and do not exceed capacities",
    "demand_violation": "total allocation is less than demand",
    "capacity_violation": "at least one supplier allocation exceeds its capacity",
    "borderline": "allocations are exactly equal or very close to limits",
}

EXAMPLES = {
    "valid": {
        "type": "valid",
        "capacities": {"S1": 500, "S2": 300},
        "demand": 600,
        "allocations": {"S1": 350, "S2": 250}
    },
    "demand_violation": {
        "type": "demand_violation",
        "capacities": {"S1": 500, "S2": 300},
        "demand": 600,
        "allocations": {"S1": 200, "S2": 150}
    },
    "capacity_violation": {
        "type": "capacity_violation",
        "capacities": {"S1": 400, "S2": 300},
        "demand": 600,
        "allocations": {"S1": 450, "S2": 150}
    },
    "borderline": {
        "type": "borderline",
        "capacities": {"S1": 500, "S2": 300},
        "demand": 600,
        "allocations": {"S1": 500, "S2": 100}
    },
}


def build_messages(dataset_type, n_samples):
    definition = DEFINITIONS[dataset_type]
    example = json.dumps(EXAMPLES[dataset_type], indent=2)

    system_content = (
        "You are a synthetic data generator. "
        "You output only valid JSON arrays, with no explanation or markdown. "
        "Each sample must have exactly these keys: type, capacities, demand, allocations."
    )

    user_content = (
        f"Generate {n_samples} samples of type '{dataset_type}'. "
        f"Definition: {definition}. "
        f"Here is one example sample (Do not copy it, treat it only as an example):\n{example}\n"
        "Return only a JSON array of samples. No explanation, no code blocks, just raw JSON."
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]
    
    
def generate_dataset(dataset_type, n_samples):
    messages = build_messages(dataset_type, n_samples)
    
    response = client.chat_completion(
        messages=messages,
        max_tokens=1024,
    )
    response_text = response.choices[0].message.content.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    
    return json.loads(response_text)

if __name__ == "__main__":
    dataset_type = "valid"  # Change to desired type
    n_samples = 5  # Change to desired number of samples
    dataset = generate_dataset(dataset_type, n_samples)
    print(json.dumps(dataset, indent=2))