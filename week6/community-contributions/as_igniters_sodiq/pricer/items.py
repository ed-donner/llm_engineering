from pydantic import BaseModel
from datasets import Dataset, DatasetDict, load_dataset
from typing import Optional, Self


PREFIX = "Price is ₦"
QUESTION = "What does this cost to the nearest naira?"

class Item(BaseModel):
    """
    An Item is a data-point of a House Rental with a Price
    """

    title: str
    city: str
    bedrooms: int
    price: float
    summary: str
        
    def make_prompt(self, text: str):
        self.prompt = f"{QUESTION}\n\n{text}\n\n{PREFIX}{round(self.price)}.00"

    def test_prompt(self) -> str:
        return self.prompt.split(PREFIX)[0] + PREFIX

    def __repr__(self) -> str:
        return f"<{self.title} = ${self.price}>"

    @staticmethod
    def push_to_hub(dataset_name: str, train: list[Self], val: list[Self], test: list[Self]):
        """Push Item lists to HuggingFace Hub"""
        DatasetDict(
            {
                "train": Dataset.from_list([item.model_dump() for item in train]),
                "validation": Dataset.from_list([item.model_dump() for item in val]),
                "test": Dataset.from_list([item.model_dump() for item in test]),
            }
        ).push_to_hub(dataset_name)

    @staticmethod
    def estimate_price_prompt(item) -> str:
        return (
            f"Estimate the yearly rent price for this house in Lagos Nigeria. "
            f"Respond with the price only, no explanation.\n\n{item.summary}"
        )

    @classmethod
    def from_hub(cls, dataset_name: str) -> tuple[list[Self], list[Self], list[Self]]:
        """Load from HuggingFace Hub and reconstruct Items"""
        ds = load_dataset(dataset_name)
        return (
            [cls.model_validate(row) for row in ds["train"]],
            [cls.model_validate(row) for row in ds["validation"]],
            [cls.model_validate(row) for row in ds["test"]],
        )