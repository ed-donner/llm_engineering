import json
from pathlib import Path
from pydantic import BaseModel, Field, field_validator

TEST_FILE = str(Path(__file__).parent / "tests.jsonl")
ALLOWED_CATEGORIES = {
    "comparative",
    "direct_fact",
    "holistic",
    "numerical",
    "relationship",
    "spanning",
    "temporal",
}


class TestQuestion(BaseModel):
    """A test question with expected keywords and reference answer."""

    question: str = Field(description="The question to ask the RAG system")
    keywords: list[str] = Field(
        description="Keywords that must appear in retrieved context"
    )
    reference_answer: str = Field(description="The reference answer for this question")
    category: str = Field(
        description="Question category (e.g., direct_fact, spanning, temporal)"
    )

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, keywords_value):
        if not keywords_value:
            raise ValueError("keywords must not be empty")
        return keywords_value

    @field_validator("category")
    @classmethod
    def validate_category(cls, category_value):
        if category_value not in ALLOWED_CATEGORIES:
            allowed = ", ".join(sorted(ALLOWED_CATEGORIES))
            raise ValueError(f"category must be one of: {allowed}")
        return category_value


def load_tests() -> list[TestQuestion]:
    """Load test questions from JSONL file."""
    tests = []
    with open(TEST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line.strip())
            tests.append(TestQuestion(**data))
    return tests


if __name__ == "__main__":
    try:
        TestQuestion(
            question="Who is Avery?",
            keywords=["Avery"],
            reference_answer="CEO of Insurellm",
            category="something else",
        )
    except Exception as e:
        print(e.errors())
        print(e.error_count())
