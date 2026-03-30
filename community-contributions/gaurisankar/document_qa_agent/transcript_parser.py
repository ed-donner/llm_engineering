import os
import sys
import types
import fitz  # PyMuPDF
from docx import Document


def read_document(file_path: str) -> str:
    """
    Unified document reader for PDF, DOCX, and TXT files.

    Args:
        file_path (str): Path to the file

    Returns:
        str: Extracted text
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Use rsplit to safely handle filenames/paths with dots in directory names
    ext = file_path.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        return _read_pdf(file_path)
    elif ext == "docx":
        return _read_docx(file_path)
    elif ext == "txt":
        return _read_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")


# -------- PDF --------
def _read_pdf(file_path: str) -> str:

    text = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text.append(page.get_text())

    return "\n".join(text)


# -------- DOCX --------
def _read_docx(file_path: str) -> str:

    doc = Document(file_path)
    text = [para.text for para in doc.paragraphs]

    return "\n".join(text)


# -------- TXT --------
def _read_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def get_file_path() -> str:
    file_path = input("Enter the file path: ").strip()
    return file_path


class CallableTranscriptParser(types.ModuleType):
    """
    Makes the module itself callable.
    When called, prompts for a file path (or accepts one) and reads the transcript.
    """

    def __call__(self, file_path: str = None) -> str:
        """
        Args:
            file_path (str, optional): The path to the document.
                Defaults to None, which will prompt the user.

        Returns:
            str: Extracted text from the document.
        """
        if file_path is None:
            file_path = get_file_path()
        return read_document(file_path)


sys.modules[__name__].__class__ = CallableTranscriptParser


def main():
    """Standalone entry point: reads a document and prints its contents."""

    def print_transcript(file_path: str):
        transcript = read_document(file_path)
        print(transcript)

    file_path = get_file_path()
    print_transcript(file_path)


if __name__ == "__main__":
    main()
