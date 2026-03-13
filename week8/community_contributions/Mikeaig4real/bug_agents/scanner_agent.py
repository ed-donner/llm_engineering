"""
CodeScannerAgent — scrapes Stack Overflow for self-contained Python bug questions.
Mirrors week8 ScannerAgent which scrapes RSS feeds from DealNews.
"""

import requests
from bs4 import BeautifulSoup
from typing import List
from bug_agents.agent import Agent
from bug_agents.models import ScrapedBug


class CodeScannerAgent(Agent):
    """Scrapes Stack Overflow for self-contained Python code with bugs."""

    name = "Code Scanner Agent"
    color = Agent.CYAN

    # Stack Overflow API endpoint
    SO_API = "https://api.stackexchange.com/2.3/questions"

    # Tags to search for — common Python bug categories
    SEARCH_TAGS = [
        "python;runtime-error",
        "python;typeerror",
        "python;nameerror",
        "python;indexerror",
    ]

    # Heavy imports to filter out (framework-dependent code)
    HEAVY_IMPORTS = {
        "django",
        "flask",
        "fastapi",
        "tensorflow",
        "keras",
        "torch",
        "pytorch",
        "pandas",
        "sqlalchemy",
        "celery",
        "scrapy",
        "cv2",
        "PIL",
        "tkinter",
        "wx",
    }

    MAX_CODE_LINES = 50
    MIN_CODE_LINES = 3

    def __init__(self):
        self.log("Code Scanner Agent is initializing")
        self.log("Code Scanner Agent is ready")

    def _fetch_questions(self, tag_set: str, page_size: int = 5) -> list:
        """Fetch recent questions from Stack Overflow API."""
        params = {
            "order": "desc",
            "sort": "creation",
            "tagged": tag_set,
            "filter": "withbody",
            "site": "stackoverflow",
            "pagesize": page_size,
        }
        try:
            resp = requests.get(self.SO_API, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json().get("items", [])
        except requests.RequestException as e:
            self.log(f"API error for tags '{tag_set}': {e}")
            return []

    def _extract_code_blocks(self, html_body: str) -> List[str]:
        """Extract <code> blocks from SO question body HTML."""
        soup = BeautifulSoup(html_body, "html.parser")
        code_blocks = []
        for code_tag in soup.find_all("code"):
            # Only grab blocks inside <pre> (multi-line code, not inline)
            if code_tag.parent and code_tag.parent.name == "pre":
                text = code_tag.get_text()
                if text.strip():
                    code_blocks.append(text.strip())
        return code_blocks

    def _is_self_contained(self, code: str) -> bool:
        """Check if code is self-contained (no heavy framework deps)."""
        lines = code.strip().split("\n")

        # Length filter
        if len(lines) < self.MIN_CODE_LINES or len(lines) > self.MAX_CODE_LINES:
            return False

        # Must contain a function or class definition
        has_def = any(line.strip().startswith(("def ", "class ")) for line in lines)
        if not has_def:
            return False

        # Filter out heavy frameworks
        code_lower = code.lower()
        for lib in self.HEAVY_IMPORTS:
            if f"import {lib}" in code_lower or f"from {lib}" in code_lower:
                return False

        return True

    def _extract_description(self, html_body: str) -> str:
        """Extract a brief text description from the SO question body."""
        soup = BeautifulSoup(html_body, "html.parser")
        # Remove code blocks to get just the description
        for tag in soup.find_all(["pre", "code"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        # Truncate to first 300 chars
        return text[:300] if text else ""

    def scan(self, memory: List[str] = []) -> List[ScrapedBug]:
        """
        Scan Stack Overflow for buggy Python code snippets.
        Returns ScrapedBug objects for each self-contained snippet found.
        """
        self.log("Scanning Stack Overflow for buggy Python code...")
        all_bugs = []
        seen_urls = set(memory)

        for tag_set in self.SEARCH_TAGS:
            self.log(f"  Searching: [{tag_set}]")
            questions = self._fetch_questions(tag_set)

            for q in questions:
                url = q.get("link", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                title = q.get("title", "Unknown")
                body = q.get("body", "")
                code_blocks = self._extract_code_blocks(body)

                for code in code_blocks:
                    if self._is_self_contained(code):
                        description = self._extract_description(body)
                        bug = ScrapedBug(
                            code=code,
                            title=title,
                            url=url,
                            description=description,
                        )
                        all_bugs.append(bug)
                        self.log(f"  ✓ Found: {title[:60]}...")
                        break  # One snippet per question

        self.log(f"Scan complete: {len(all_bugs)} self-contained bugs found")
        return all_bugs

    def test_scan(self) -> List[ScrapedBug]:
        """Return test data for development without hitting the API."""
        return [
            ScrapedBug(
                code="def calculate_average(numbers):\n    if not numbers:\n        return 0\n    total_sum = sum(numers)\n    count = len(numbers) - 1\n    return total_sum / count",
                title="NameError in calculate_average function",
                url="https://stackoverflow.com/questions/test1",
                description="My function to calculate average throws a NameError",
            ),
            ScrapedBug(
                code='def find_maximum(numbers):\n    if not numbers\n        raise ValueError("The array cannot be empty.")\n    maximum_value = numbers[0]\n    for number in number:\n        if number > maximum_value:\n            maximum_value = number\n    return maximum_value',
                title="SyntaxError and NameError in find_maximum",
                url="https://stackoverflow.com/questions/test2",
                description="Getting syntax error and name error in my max finder",
            ),
        ]
