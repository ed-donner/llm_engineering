import re
from typing import List
import logging

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  ACADEMIC HEADINGS
# ------------------------------------------------------------------ #

ACADEMIC_HEADINGS = [
    "Abstract",
    "Introduction",
    "Related Work",
    "Background",
    "Preliminaries",
    "Problem Statement",
    "Problem Formulation",
    "Method",
    "Methods",
    "Methodology",
    "Proposed Method",
    "Proposed Approach",
    "Approach",
    "Model",
    "Model Architecture",
    "Architecture",
    "Framework",
    "System Design",
    "Implementation",
    "Training",
    "Training Details",
    "Experiments",
    "Experimental Setup",
    "Experimental Results",
    "Setup",
    "Datasets",
    "Data",
    "Evaluation",
    "Results",
    "Results and Discussion",
    "Analysis",
    "Ablation Study",
    "Ablation",
    "Discussion",
    "Limitations",
    "Future Work",
    "Conclusion",
    "Conclusions",
    "Conclusion and Future Work",
    "Acknowledgements",
    "Acknowledgments",
    "References",
    "Appendix",
]


class StructureDetector:
    """
    Detects structure from extracted markdown text.

    Supports:
    - markdown headers
    - academic section headings
    - book vs paper detection
    - structure-aware section splitting
    """

    # ------------------------------------------------------------------ #
    #  DETECTION
    # ------------------------------------------------------------------ #

    def detect(self, text: str) -> dict:
        md_headers = self.get_markdown_headers(text)
        ac_headings = self.get_academic_headings(text)

        has_md = len(md_headers) > 0
        has_ac = len(ac_headings) > 0

        doc_type = self._detect_document_type(
            text=text,
            markdown_headers=md_headers,
            academic_headings=ac_headings,
        )

        # Strategy selection
        if has_ac and len(ac_headings) >= 3:
            strategy = "section"
        elif has_md and len(md_headers) >= 3:
            strategy = "header"
        else:
            strategy = "text_splitter"

        return {
            "has_markdown_headers": has_md,
            "has_academic_headings": has_ac,
            "document_type": doc_type,
            "markdown_headers": md_headers,
            "academic_headings": ac_headings,
            "recommended_strategy": strategy,
        }

    # ------------------------------------------------------------------ #
    #  DOCUMENT TYPE DETECTION
    # ------------------------------------------------------------------ #

    def _detect_document_type(
        self,
        text: str,
        markdown_headers: List[str],
        academic_headings: List[str],
    ) -> str:
        """
        Heuristic detection:
        - research_paper
        - book
        - unknown
        """

        text_lower = text.lower()

        paper_score = 0
        book_score = 0

        # -----------------------------
        # Paper signals
        # -----------------------------

        if len(academic_headings) >= 3:
            paper_score += 3

        paper_patterns = [
            r"\[\d+\]",        # citations [1]
            r"et al\.",
            r"\breferences\b",
            r"\bconference\b",
            r"\bjournal\b",
            r"\bdoi\b",
        ]

        for pattern in paper_patterns:
            if re.search(pattern, text_lower):
                paper_score += 1

        # -----------------------------
        # Book signals
        # -----------------------------

        book_patterns = [
            r"\bchapter\s+\d+\b",
            r"\bexercise\b",
            r"\bexample\b",
            r"\blearning objectives\b",
            r"\breview questions\b",
            r"\bkey points\b",
        ]

        for pattern in book_patterns:
            if re.search(pattern, text_lower):
                book_score += 1

        if len(markdown_headers) >= 8:
            book_score += 1

        # -----------------------------
        # Final decision
        # -----------------------------

        if paper_score >= max(book_score, 3):
            return "research_paper"

        if book_score >= 2:
            return "book"

        return "unknown"

    # ------------------------------------------------------------------ #
    #  HEADER EXTRACTION
    # ------------------------------------------------------------------ #

    def has_markdown_headers(self, text: str) -> bool:
        pattern = r"^\s{0,3}#{1,6}\s+\S+"
        return bool(re.search(pattern, text, flags=re.MULTILINE))

    def get_markdown_headers(self, text: str) -> List[str]:
        """
        Returns markdown headers while skipping equation-like fake headers.
        """

        pattern = r"^\s{0,3}#{1,6}\s+.+$"
        matches = re.findall(pattern, text, flags=re.MULTILINE)

        cleaned = []

        for header in matches:
            plain = re.sub(r"^\s{0,3}#{1,6}\s+", "", header)
            plain = plain.replace("**", "").strip()

            looks_like_equation = (
                "=" in plain
                or "softmax" in plain.lower()
                or "max(" in plain.lower()
                or any(sym in plain for sym in ["W_", "_b", "\\"])
            )

            too_mathy = sum(ch in plain for ch in "=+-*/_()[]{}") >= 4

            if looks_like_equation or too_mathy:
                continue

            cleaned.append(header)

        return cleaned

    def has_academic_headings(self, text: str) -> bool:
        for heading in ACADEMIC_HEADINGS:
            pattern = rf"^\s*(\d+\.?\s+)?{re.escape(heading)}\s*$"

            if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
                return True

        return False

    def get_academic_headings(self, text: str) -> List[str]:
        found = []

        for heading in ACADEMIC_HEADINGS:
            pattern = rf"^\s*(\d+\.?\s+)?{re.escape(heading)}\s*$"

            if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
                found.append(heading)

        return found

    # ------------------------------------------------------------------ #
    #  SECTION SPLITTING
    # ------------------------------------------------------------------ #

    def split_by_sections(self, text: str) -> List[dict]:
        heading_patterns = []

        for heading in ACADEMIC_HEADINGS:
            heading_patterns.append(
                rf"(?:\d+\.?\s+)?{re.escape(heading)}"
            )

        combined = "|".join(heading_patterns)

        pattern = rf"^\s*({combined})\s*$"

        matches = list(
            re.finditer(
                pattern,
                text,
                flags=re.IGNORECASE | re.MULTILINE,
            )
        )

        if not matches:
            return [{
                "section_title": "Full Document",
                "content": text,
                "page_start": self._first_page(text),
                "page_end": self._last_page(text),
            }]

        sections = []

        pre_content = text[:matches[0].start()].strip()

        if len(pre_content) > 100:
            sections.append({
                "section_title": "Preamble",
                "content": pre_content,
                "page_start": self._first_page(pre_content),
                "page_end": self._last_page(pre_content),
            })

        for i, match in enumerate(matches):
            title = match.group(0).strip()

            clean_title = re.sub(
                r"^\d+\.?\s+",
                "",
                title,
            ).strip()

            start = match.end()

            end = (
                matches[i + 1].start()
                if i + 1 < len(matches)
                else len(text)
            )

            section_block = text[match.start():end].strip()
            content = text[start:end].strip()

            if len(content) < 20:
                continue

            sections.append({
                "section_title": clean_title,
                "content": content,
                "page_start": self._first_page(section_block),
                "page_end": self._last_page(section_block),
            })
        print(f"detector.split by sec called: section = {sections}")

        logger.info(f"Split into {len(sections)} sections")
        self._fill_missing_pages(sections)
        return sections

    def split_by_headers(self, text: str) -> List[dict]:
        pattern = r"^\s{0,3}(#{1,6})\s+(.+)$"

        matches = list(
            re.finditer(
                pattern,
                text,
                flags=re.MULTILINE,
            )
        )

        if not matches:
            return [{
                "section_title": "Full Document",
                "content": text,
                "page_start": self._first_page(text),
                "page_end": self._last_page(text),
            }]

        sections = []

        pre_content = text[:matches[0].start()].strip()

        if len(pre_content) > 100:
            sections.append({
                "section_title": "Preamble",
                "content": pre_content,
                "page_start": self._first_page(pre_content),
                "page_end": self._last_page(pre_content),
            })

        for i, match in enumerate(matches):
            title = match.group(2).strip()

            title = re.sub(
                r"\*\*(.+?)\*\*",
                r"\1",
                title,
            )

            # Skip equation-like headers
            looks_like_equation = bool(
                re.match(r"^[^a-zA-Z]*=", title)          # starts with symbols then =
                or re.match(r"^\s*\w+\s*\(.*\)\s*=", title)  # f(x) = ... pattern
            )

            if looks_like_equation:
                continue

            start = match.end()

            end = (
                matches[i + 1].start()
                if i + 1 < len(matches)
                else len(text)
            )

            section_block = text[match.start():end].strip()
            content = text[start:end].strip()

            if len(content) < 20:
                continue

            sections.append({
                "section_title": title,
                "content": content,
                "page_start": self._first_page(section_block),
                "page_end": self._last_page(section_block),
            })
        print(f"detector.split by headers called: section = {sections}")
        logger.info(f"Split into {len(sections)} header sections")
        self._fill_missing_pages(sections)
        return sections

    # ------------------------------------------------------------------ #
    #  HELPERS
    # ------------------------------------------------------------------ #

    def _first_page(self, content: str) -> int:
        markers = re.findall(r'\[Page (\d+)\]', content)
        return int(markers[0]) if markers else 0

    def _last_page(self, content: str) -> int:
        markers = re.findall(r'\[Page (\d+)\]', content)
        return int(markers[-1]) if markers else 0

    def _fill_missing_pages(self, sections: List[dict]) -> None:
        # Forward pass
        last_known = 0
        for section in sections:
            if section["page_start"] != 0:
                last_known = section["page_start"]
            elif last_known != 0:
                section["page_start"] = last_known

            if section["page_end"] != 0:
                last_known = section["page_end"]
            elif last_known != 0:
                section["page_end"] = section["page_start"]

        # Backward pass
        first_known = 0
        for section in reversed(sections):
            if section["page_start"] != 0:
                first_known = section["page_start"]
            elif first_known != 0:
                section["page_start"] = first_known

            if section["page_end"] != 0:
                first_known = section["page_end"]
            elif first_known != 0:
                section["page_end"] = section["page_start"]