import pdfplumber
import logging
import re

logger = logging.getLogger(__name__)

def looks_like_broken_table(content: str) -> bool:
    corruption_patterns = [
        r"\|\s*ehT\s*\|",
        r"\|\s*waL\s*\|",
        r">\s*SOE<",
        r">\s*pad<",
    ]

    if any(re.search(pattern, content) for pattern in corruption_patterns):
        return True

    lines = content.splitlines()
    table_lines = [line for line in lines if line.strip().startswith("|")]

    if not table_lines:
        return False

    # Pipe-separated lines without markdown header separator = raw dump
    has_separator = any("---" in line for line in table_lines)
    if not has_separator and len(table_lines) >= 2:
        return True

    if len(table_lines) < 5:
        return False

    tiny_cells = 0
    total_cells = 0
    empty_cells = 0
    weird_cells = 0
    max_columns = 0

    for line in table_lines:
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        total_cells += len(cells)
        max_columns = max(max_columns, len(cells))

        for cell in cells:
            if not cell:
                empty_cells += 1
            elif len(cell) <= 3:
                tiny_cells += 1
            if re.fullmatch(r"[A-Za-z]{1,4}", cell):
                weird_cells += 1

    if total_cells == 0:
        return False

    tiny_ratio = tiny_cells / total_cells
    empty_ratio = empty_cells / total_cells
    weird_ratio = weird_cells / total_cells

    return (
        tiny_ratio > 0.60
        or empty_ratio > 0.75
        or weird_ratio > 0.75
        or max_columns > 20
    )
    
class TableExtractor:
    """
    Extracts tables from PDFs using pdfplumber and converts
    them to clean markdown strings ready for embedding.

    Skips:
    - broken OCR/extraction-noise tables
    - giant meaningless tables
    - appendix/reference-heavy pages
    """

    def extract(self, pdf_path: str) -> dict:
        tables_by_page = {}

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_num = i + 1
                    raw_tables = page.extract_tables()

                    md_tables = []

                    for table in raw_tables:
                        if not table or len(table) < 2:
                            continue

                        md = self._to_markdown(table)

                        if not md:
                            continue

                        if looks_like_broken_table(md):
                            continue

                        md_tables.append(md)

                    if not md_tables:
                        continue

                    if self._looks_like_appendix(page, md_tables):
                        continue

                    tables_by_page[page_num] = md_tables

        except Exception as e:
            logger.warning(f"Table extraction failed for {pdf_path}: {e}")

        return tables_by_page
    
    def _looks_like_appendix(self, page, md_tables: list[str]) -> bool:
        try:
            text = (page.extract_text() or "").lower()
        except Exception:
            return False

        appendix_signals = [
            "appendix",
            "supplementary",
            "references",
            "bibliography",
            "acknowledgements",
            "acknowledgments",
            "additional results",
        ]

        if any(signal in text for signal in appendix_signals):
            return True

        if len(md_tables) >= 4:
            return True

        return False

    def _to_markdown(self, table: list) -> str:
        if not table or len(table) < 2:
            return ""

        table = [
            row for row in table
            if row and any(str(cell or "").strip() for cell in row)
        ]

        if len(table) < 2:
            return ""

        header_cells = [self._clean_cell(cell) for cell in table[0]]

        if len(header_cells) > 12 and sum(bool(c) for c in header_cells) < 2:
            return ""

        header = "| " + " | ".join(header_cells) + " |"
        separator = "| " + " | ".join("---" for _ in header_cells) + " |"

        rows = []

        for row in table[1:]:
            row_cells = [self._clean_cell(cell) for cell in row]

            if len(row_cells) < len(header_cells):
                row_cells += [""] * (len(header_cells) - len(row_cells))
            elif len(row_cells) > len(header_cells):
                row_cells = row_cells[:len(header_cells)]

            rows.append("| " + " | ".join(row_cells) + " |")

        return "\n".join([header, separator] + rows)

    def _clean_cell(self, cell) -> str:
        text = str(cell or "").strip()
        text = text.replace("<br>", " ")
        text = text.replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        text = text.replace("|", " ")
        return text.strip()



