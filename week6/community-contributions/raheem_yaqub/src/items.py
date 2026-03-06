from pydantic import BaseModel
from datasets import Dataset, DatasetDict, load_dataset
from typing import Optional, Self


class LoadData(BaseModel):

    title: str
    company: str
    location: str
    experience: str
    skills: str
    salary: float
    description: str
    prompt: str | None = None


    @staticmethod
    def from_hub_train(dataset_name):

        dataset = load_dataset(dataset_name)

        return [LoadData(**row) for row in dataset["train"]]

    @classmethod
    def from_hub_test(cls, dataset_name):
        dataset = load_dataset(dataset_name)
        return [LoadData(**row) for row in dataset["test"]]