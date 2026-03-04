"""
ULTRA DUMMIE DESCRIPTION
------------------------
What this file does:
- Defines the structure of one evaluation test case.
- Loads all test cases from tests.jsonl.

Internal steps:
1) Defines a Pydantic model with question, keywords, reference answer, and category.
2) Reads tests.jsonl line by line.
3) Parses each JSON line and validates it with Pydantic.
4) Returns a list of validated test objects.

Key logic:
- This file does not run evaluation by itself.
- It only prepares clean test data for eval2.py.
"""

import json  # Imports JSON parser to read one test per line from file.
from pathlib import Path  # Imports Path for robust path handling.
from pydantic import BaseModel, Field  # Imports Pydantic classes for validation and field metadata.

TEST_FILE = str(Path(__file__).parent / "tests.jsonl")  # Builds absolute path to the JSONL test file.
DEBUG = True  # Enables or disables debug logs for this module.


def dbg(message):  # Defines helper to print debug traces only when DEBUG is active.
    if DEBUG:  # Checks debug flag.
        print(f"[TEST] {message}")  # Prints log line with module prefix.


class TestQuestion(BaseModel):  # Defines one validated evaluation test item.
    """A test question with expected keywords and reference answer."""  # Describes model purpose.

    question: str = Field(description="The question to ask the RAG system")  # Stores the user question to evaluate.
    keywords: list[str] = Field(description="Keywords that must appear in retrieved context")  # Stores retrieval keywords expected in context.
    reference_answer: str = Field(description="The reference answer for this question")  # Stores the expected canonical answer.
    category: str = Field(description="Question category (e.g., direct_fact, spanning, temporal)")  # Stores test category label.


def load_tests() -> list[TestQuestion]:  # Defines function to load and validate all tests from JSONL.
    """Load test questions from JSONL file."""  # Documents function behavior.
    dbg(f"Loading tests from: {TEST_FILE}")  # Traces source file path.
    tests = []  # Initializes output list for validated tests.
    with open(TEST_FILE, "r", encoding="utf-8") as f:  # Opens JSONL file in UTF-8 mode.
        for line_number, line in enumerate(f, start=1):  # Iterates lines with 1-based index for diagnostics.
            stripped = line.strip()  # Removes whitespace/newline around current line.
            if not stripped:  # Checks if line is empty.
                dbg(f"Skipping empty line at {line_number}")  # Traces skipped empty lines.
                continue  # Moves to next line.
            data = json.loads(stripped)  # Parses JSON object from current line text.
            tests.append(TestQuestion(**data))  # Validates and appends parsed test object.
    dbg(f"Loaded tests: {len(tests)}")  # Traces total number of loaded tests.
    return tests  # Returns validated list of test questions.
