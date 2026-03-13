"""
Bug-RAG test loader; loads from evals/tests.jsonl.
"""
import json
from pathlib import Path
from pydantic import BaseModel, Field

TEST_FILE = str(Path(__file__).parent / "tests.jsonl")


class TestQuestion(BaseModel):
    """A test question with expected keywords and reference answer."""

    question: str = Field(description="The question to ask the RAG system")
    keywords: list[str] = Field(description="Keywords that must appear in retrieved context")
    reference_answer: str = Field(description="The reference answer for this question")
    category: str = Field(description="Question category (e.g., when, where, how, holistic)")


def load_tests(path: str | None = None) -> list[TestQuestion]:
    """Load test questions from JSONL file. Defaults to evals/tests.jsonl."""
    filepath = path or TEST_FILE
    tests = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line.strip())
            tests.append(TestQuestion(**data))
    return tests
