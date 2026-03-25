import json
from pathlib import Path
from pydantic import BaseModel, Field

TEST_FILE = Path(__file__).parent / "tests.jsonl"


class TestQuestion(BaseModel):
    question: str = Field(description="The question to ask the RAG system")
    keywords: list[str] = Field(description="Keywords that must appear in retrieved context")
    reference_answer: str = Field(description="The reference answer for this question")
    category: str = Field(description="Question category (e.g. fees, admissions, general)")


def load_tests(path: Path | None = None) -> list[TestQuestion]:
    p = path if path is not None else TEST_FILE
    tests = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line.strip())
            tests.append(TestQuestion(**data))
    return tests


def save_tests(tests: list[TestQuestion], path: Path | None = None) -> None:
    p = path if path is not None else TEST_FILE
    with open(p, "w", encoding="utf-8") as f:
        for t in tests:
            f.write(t.model_dump_json() + "\n")
