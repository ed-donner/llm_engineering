import json
import os

DEFAULT_HASH_FILE = os.path.join(os.path.dirname(__file__), "file_hashes.json")


def load_hash(file_path=DEFAULT_HASH_FILE):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r") as f:
        return json.load(f)


def save_hash(data, file_path=DEFAULT_HASH_FILE):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)