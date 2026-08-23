from pydantic import BaseModel, ConfigDict
from datasets import Dataset, DatasetDict, load_dataset
from typing import Optional, Self


PREFIX = "Salary is $"
QUESTION = "What is the salary to the nearest dollar?"


class Item(BaseModel):

    model_config = ConfigDict(extra="ignore")

    title: str
    company: str
    location: str
    experience: str
    skills: str
    salary: float
    description: str
    prompt: Optional[str] = None

    def make_prompt(self, text: str):
        self.prompt = f"{QUESTION}\n\n{text}\n\n{PREFIX}{round(self.salary)}.00"

    def test_prompt(self) -> str:
        return self.prompt.split(PREFIX)[0] + PREFIX

    def __repr__(self) -> str:
        return f"<{self.title} = ${self.salary}>"

    @staticmethod
    def push_to_hub(dataset_name: str, train: list[Self], val: list[Self], test: list[Self]):

        DatasetDict(
            {
                "train": Dataset.from_list([item.model_dump() for item in train]),
                "validation": Dataset.from_list([item.model_dump() for item in val]),
                "test": Dataset.from_list([item.model_dump() for item in test]),
            }
        ).push_to_hub(dataset_name)

    @classmethod
    def from_hub(cls, dataset_name: str):

        ds = load_dataset(dataset_name)

        return (
            [cls.model_validate(row, by_name=True) for row in ds["train"]],
            [cls.model_validate(row, by_name=True) for row in ds["validation"]],
            [cls.model_validate(row, by_name=True) for row in ds["test"]],
        )