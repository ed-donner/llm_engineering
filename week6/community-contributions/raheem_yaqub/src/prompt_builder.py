import json


def create_training_jsonl(items, path):

    with open(path, "w") as f:

        for item in items:

            if not all([
                item.title,
                item.company,
                item.location,
                item.skills,
                item.experience,
                item.salary
            ]):
                continue

            item.make_prompt()

            example = {
                "messages": [
                    {"role": "user", "content": item.test_prompt()},
                    {"role": "assistant", "content": str(int(item.salary))}
                ]
            }

            f.write(json.dumps(example) + "\n")