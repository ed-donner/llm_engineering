import json
from pathlib import Path

from pydantic import BaseModel, Field

TEST_FILE = Path(__file__).parent / "tests.jsonl"


class TestQuestion(BaseModel):
    """A test question with expected keywords and reference answer."""

    question: str = Field(description="The question to ask the RAG system")
    keywords: list[str] = Field(description="Keywords expected in retrieved context")
    reference_answer: str = Field(description="Reference answer for LLM-judge comparison")
    category: str = Field(description="Question category (direct_fact, how_to, comparison, etc.)")


def load_tests(path: str | Path | None = None) -> list[TestQuestion]:
    """Load test questions from JSONL file."""
    file_path = Path(path) if path else TEST_FILE
    tests: list[TestQuestion] = []
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            tests.append(TestQuestion(**json.loads(line)))
    return tests
