import pymupdf # PyMuPDF
def extract_text(pdf_path):
    """
    Extracts and aggregates text from all pages of a given PDF file while displaying
    metadata including title and author.

    This function opens a PDF file, extracts text from every page, and combines the text
    into a single string for further use. Metadata such as the document title and author
    will also be printed for informational purposes. The PDF file is closed automatically
    once the operation is complete.

    Parameters:
        pdf_path (str): The file path to the PDF document.

    Returns:
        str: A compiled string of text extracted from all pages of the PDF.
    """
    # Replace 'your_document.pdf' with the actual path to your PDF file
    doc = pymupdf.open(pdf_path)
    print(f"Document title: {doc.metadata['title']}")
    print(f"Document author: {doc.metadata['author']}")

    # Extract text from all pages
    all_text = ""
    for page in doc:
        all_text += page.get_text() + "\n"
    print("\nText from all pages:")
    print(all_text)

    doc.close()
    return all_text