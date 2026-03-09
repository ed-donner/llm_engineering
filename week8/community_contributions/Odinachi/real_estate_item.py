from pydantic import BaseModel
from datasets import Dataset, DatasetDict, load_dataset
from typing import Optional, Self


PREFIX = "Price is $"
QUESTION = "What does this cost to the nearest dollar?"


class RealEstateItem(BaseModel):
    """
    An Item is a data-point of a Product with a Price
    """

    rooms: str
    bathrooms: str
    price: Optional[float] = None
    price_range_low: Optional[float] = None
    price_range_high: Optional[float] = None
    country: Optional[str] = None
    state: Optional[str] = None
    size: Optional[str] = None
    property_type: Optional[str] = None
    year_built: Optional[str] = None
    neighborhood_type: Optional[str] = None
    condition: Optional[str] = None
    school_rating: Optional[str] = None
    description: Optional[str] = None
    id: Optional[int] = None

  

    def __repr__(self) -> str:
        return f"<{self.rooms} rooms, {self.bathrooms} bathrooms, ${self.price}>"

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

    @classmethod
    def from_hub(cls, dataset_name: str) -> tuple[list[Self], list[Self], list[Self]]:
        """Load from HuggingFace Hub and reconstruct Items"""
        ds = load_dataset(dataset_name)
        return (
            [cls.model_validate(row) for row in ds["train"]],
            [cls.model_validate(row) for row in ds["validation"]],
            [cls.model_validate(row) for row in ds["test"]],
        )


class PromptedRealEstateItem(BaseModel):
    """
    A PromptedRealEstateItem is a data-point of a Product with a Price
    """

    input_text: str
    output_text: str
    
    
    
    def __repr__(self) -> str:
        return f"<Input: {self.input_text} = {self.output_text}>"
