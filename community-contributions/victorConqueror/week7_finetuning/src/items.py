"""Item class for handling product data"""

from pydantic import BaseModel
from datasets import Dataset, DatasetDict, load_dataset
from typing import Optional, Self


class Item(BaseModel):
    """
    An Item represents a product with price information
    Used for training and evaluation
    """

    title: str
    category: str
    price: float
    full: Optional[str] = None
    weight: Optional[float] = None
    summary: Optional[str] = None
    prompt: Optional[str] = None
    completion: Optional[str] = None
    id: Optional[int] = None

    def __repr__(self) -> str:
        return f"<{self.title[:40]}... = ${self.price:.2f}>"

    def count_tokens(self, tokenizer) -> int:
        """Count tokens in the summary"""
        if not self.summary:
            return 0
        return len(tokenizer.encode(self.summary, add_special_tokens=False))

    def make_prompts(self, tokenizer, max_tokens: int, do_round: bool = True):
        """
        Create prompt-completion pairs for training
        
        Args:
            tokenizer: HuggingFace tokenizer
            max_tokens: Maximum tokens for summary (truncate if longer)
            do_round: Whether to round price to nearest dollar
        """
        # Truncate summary if too long
        tokens = tokenizer.encode(self.summary, add_special_tokens=False)
        if len(tokens) > max_tokens:
            summary = tokenizer.decode(tokens[:max_tokens]).rstrip()
        else:
            summary = self.summary
        
        # Create prompt and completion
        from .config import config
        self.prompt = f"{config.QUESTION}\n\n{summary}\n\n{config.PREFIX}"
        self.completion = f"{round(self.price)}.00" if do_round else f"{self.price:.2f}"

    def count_prompt_tokens(self, tokenizer) -> int:
        """Count tokens in full prompt + completion"""
        if not self.prompt or not self.completion:
            return 0
        full = self.prompt + self.completion
        return len(tokenizer.encode(full, add_special_tokens=False))

    def test_prompt(self) -> str:
        """Get prompt without completion (for inference)"""
        if not self.prompt:
            return ""
        from .config import config
        return self.prompt.split(config.PREFIX)[0] + config.PREFIX

    def to_datapoint(self) -> dict:
        """Convert to dictionary for dataset"""
        return {
            "prompt": self.prompt,
            "completion": self.completion
        }

    @staticmethod
    def push_to_hub(dataset_name: str, train: list[Self], val: list[Self], test: list[Self]):
        """Push Item lists to HuggingFace Hub"""
        DatasetDict({
            "train": Dataset.from_list([item.model_dump() for item in train]),
            "validation": Dataset.from_list([item.model_dump() for item in val]),
            "test": Dataset.from_list([item.model_dump() for item in test]),
        }).push_to_hub(dataset_name)

    @classmethod
    def from_hub(cls, dataset_name: str) -> tuple[list[Self], list[Self], list[Self]]:
        """Load from HuggingFace Hub and reconstruct Items"""
        ds = load_dataset(dataset_name)
        return (
            [cls.model_validate(row) for row in ds["train"]],
            [cls.model_validate(row) for row in ds["validation"]],
            [cls.model_validate(row) for row in ds["test"]],
        )

    @staticmethod
    def push_prompts_to_hub(
        dataset_name: str, 
        train: list[Self], 
        val: list[Self], 
        test: list[Self]
    ):
        """Push prompt-completion pairs to HuggingFace Hub for SFT training"""
        DatasetDict({
            "train": Dataset.from_list([item.to_datapoint() for item in train]),
            "val": Dataset.from_list([item.to_datapoint() for item in val]),
            "test": Dataset.from_list([item.to_datapoint() for item in test]),
        }).push_to_hub(dataset_name)

    @classmethod
    def load_prompts_from_hub(cls, dataset_name: str) -> tuple[list[dict], list[dict], list[dict]]:
        """Load prompt-completion pairs from HuggingFace Hub"""
        ds = load_dataset(dataset_name)
        return (
            list(ds["train"]),
            list(ds["val"]),
            list(ds["test"]),
        )
