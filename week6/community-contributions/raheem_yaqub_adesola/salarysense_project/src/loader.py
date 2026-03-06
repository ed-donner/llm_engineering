from datasets import load_dataset
from src.parser import parse
from tqdm import tqdm


def load_jobs(dataset_name):

    dataset = load_dataset(dataset_name)["train"]

    items = []

    for row in tqdm(dataset):

        item = parse(row)

        if item is not None:
            items.append(item)

    return items