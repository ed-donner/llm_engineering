import json
from openai import OpenAI
from dotenv import load_dotenv
import os
from huggingface_hub import login

load_dotenv(override=True)
hf_token = os.getenv('HF_TOKEN')
login(token=hf_token)

from datasets import load_dataset

ds = load_dataset("ayanmukherjee/repliqa-4-company-policies-answerable")

fine_tune_train = []
fine_tune_val = []

for item in ds["train"]:
    fine_tune_train.append(item)

for item in ds["validation"]:
    fine_tune_val.append(item)


def construct_msg(item):
    return [
        {"role": "user", "content": item["question"]},
        {"role": "assistant", "content": item["long_answer"]}
    ]

def make_jsonl(items):
    result = ""
    for item in items:
        messages = construct_msg(item)
        messages_str = json.dumps(messages)
        result += '{"messages": ' + messages_str +'}\n'
    return result.strip()

def write_jsonl(items, filename):
    with open(filename, "w") as f:
        jsonl = make_jsonl(items)
        f.write(jsonl)

write_jsonl(fine_tune_train, "jsonl/fine_tune_train.jsonl")
write_jsonl(fine_tune_val, "jsonl/fine_tune_validation.jsonl")

openai = OpenAI()

with open("jsonl/fine_tune_train.jsonl", "rb") as f:
    train_file = openai.files.create(file=f, purpose="fine-tune")

with open("jsonl/fine_tune_validation.jsonl", "rb") as f:
    validation_file = openai.files.create(file=f, purpose="fine-tune")

openai.fine_tuning.jobs.create(
    training_file=train_file.id,
    validation_file=validation_file.id,
    model="gpt-4.1-nano-2025-04-14",
    seed=42,
    hyperparameters={"n_epochs": 1, "batch_size": 1},
    suffix="company-policy-chatbot"
)

# After fine-tuning is complete, we can obtain the finetuned model name from OpenAI API Platforms and use it.