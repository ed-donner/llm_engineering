import pymupdf


def extract_pdf_text(pdf_path: str) -> str:
    """
    Extract text from PDF using PyMuPDF.
    """

    text = []

    with pymupdf.open(pdf_path) as doc:

        for page in doc:
            page_text = page.get_text()

            if page_text:
                text.append(page_text)

    return "\n".join(text)
