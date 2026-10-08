"""
Test question loader for the Hospital-Ashir RAG evaluation suite.
"""

import json
from pathlib import Path
from pydantic import BaseModel, Field

TEST_FILE = str(Path(__file__).parent / "tests.jsonl")


class TestQuestion(BaseModel):
    """A test question with expected keywords and reference answer."""

    question: str = Field(description="The question to ask the RAG system")
    keywords: list[str] = Field(
        description="Keywords that must appear in retrieved context (case-insensitive substring match)"
    )
    reference_answer: str = Field(description="The reference answer for this question")
    category: str = Field(
        description="Question category (e.g., direct_fact, doctor_info, patient_info, disease_program, spanning)"
    )


def load_tests(path: str | None = None) -> list[TestQuestion]:
    """Load test questions from a JSONL file (defaults to ./tests.jsonl)."""
    file_path = Path(path) if path else Path(TEST_FILE)

    if not file_path.is_absolute():
        file_path = Path(__file__).parent / file_path

    tests: list[TestQuestion] = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            tests.append(TestQuestion(**data))
    return tests
