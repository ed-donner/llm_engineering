import re
from pypdf import PdfReader


def extract_pdf_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)

    text = []

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            # Fix line breaks inside words
            page_text = re.sub(r"(\w)-\n(\w)", r"\1\2", page_text)

            # Replace newlines with spaces
            page_text = page_text.replace("\n", " ")

            # Normalize multiple spaces
            page_text = re.sub(r"\s+", " ", page_text)

            text.append(page_text)

    return "\n".join(text)