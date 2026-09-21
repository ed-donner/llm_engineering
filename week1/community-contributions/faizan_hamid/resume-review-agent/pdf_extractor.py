from pypdf import PdfReader

def extract_text_from_pdf(pdf_path):
    """
    Extract text from all pages of a PDF and return as a single string.
    """
    reader = PdfReader(pdf_path)
    extracted_text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            extracted_text.append(page_text)
    return "\n".join(extracted_text)