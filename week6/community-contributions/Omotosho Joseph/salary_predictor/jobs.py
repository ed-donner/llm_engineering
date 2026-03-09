from pydantic import BaseModel
from datasets import Dataset, DatasetDict, load_dataset
from typing import Optional, Self


PREFIX = "Salary is $"
QUESTION = "What is the annual salary for this position to the nearest thousand dollars?"


class Job(BaseModel):
    """
    A Job is a data-point of a Job Posting with a Salary
    """

    title: str
    category: str
    salary: float
    full: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    skills: Optional[str] = None
    schedule_type: Optional[str] = None
    work_from_home: Optional[bool] = None
    summary: Optional[str] = None
    prompt: Optional[str] = None
    id: Optional[int] = None

    def make_prompt(self, text: str):
        self.prompt = f"{QUESTION}\n\n{text}\n\n{PREFIX}{round(self.salary / 1000) * 1000:.0f}"

    def test_prompt(self) -> str:
        return self.prompt.split(PREFIX)[0] + PREFIX

    def __repr__(self) -> str:
        return f"<{self.title} = ${self.salary:,.0f}>"

    @staticmethod
    def push_to_hub(dataset_name: str, train: list[Self], val: list[Self], test: list[Self]):
        """Push Job lists to HuggingFace Hub"""
        DatasetDict(
            {
                "train": Dataset.from_list([job.model_dump() for job in train]),
                "validation": Dataset.from_list([job.model_dump() for job in val]),
                "test": Dataset.from_list([job.model_dump() for job in test]),
            }
        ).push_to_hub(dataset_name)

    @classmethod
    def from_hub(cls, dataset_name: str) -> tuple[list[Self], list[Self], list[Self]]:
        """Load from HuggingFace Hub and reconstruct Jobs"""
        ds = load_dataset(dataset_name)
        return (
            [cls.model_validate(row) for row in ds["train"]],
            [cls.model_validate(row) for row in ds["validation"]],
            [cls.model_validate(row) for row in ds["test"]],
        )
