"""Job data model for salary estimation."""

from pydantic import BaseModel
from datasets import Dataset, DatasetDict, load_dataset
from typing import Optional, Self


class Job(BaseModel):
    """
    A Job is a data-point with a job description and salary.
    """

    title: str
    category: str  # job_title_short or role type
    salary: float  # yearly salary in USD
    full: Optional[str] = None  # raw concatenated job text
    summary: Optional[str] = None  # LLM-rewritten concise description
    company: Optional[str] = None
    location: Optional[str] = None
    remote: Optional[bool] = None
    id: Optional[int] = None

    def __repr__(self) -> str:
        return f"<{self.title} @ ${self.salary:,.0f}>"

    @staticmethod
    def push_to_hub(
        dataset_name: str,
        train: list[Self],
        val: list[Self],
        test: list[Self],
    ):
        """Push Job lists to HuggingFace Hub."""
        DatasetDict(
            {
                "train": Dataset.from_list([job.model_dump() for job in train]),
                "validation": Dataset.from_list([job.model_dump() for job in val]),
                "test": Dataset.from_list([job.model_dump() for job in test]),
            }
        ).push_to_hub(dataset_name)

    @classmethod
    def from_hub(cls, dataset_name: str) -> tuple[list[Self], list[Self], list[Self]]:
        """Load from HuggingFace Hub and reconstruct Jobs."""
        ds = load_dataset(dataset_name)
        return (
            [cls.model_validate(row) for row in ds["train"]],
            [cls.model_validate(row) for row in ds["validation"]],
            [cls.model_validate(row) for row in ds["test"]],
        )
