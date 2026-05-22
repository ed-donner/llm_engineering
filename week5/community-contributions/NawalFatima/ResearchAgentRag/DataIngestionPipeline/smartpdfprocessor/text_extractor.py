import pymupdf4llm
import re
import logging

logger = logging.getLogger(__name__)


class TextExtractor:
    """
    Handles PDF text extraction via pymupdf4llm.
    Single pass — extracts clean markdown text and writes
    image files to img_dir simultaneously.
    """

    def extract(self, pdf_path: str, img_dir: str) -> list:
        """
        Extracts markdown text and images from a PDF in one pass.

        Returns a list of page dicts:
            {
                "text": str,        ← markdown text for this page
                "metadata": dict,   ← pymupdf4llm page metadata
                "images": list,     ← image records (path, bbox, etc.)
            }

        Images are written as PNG files to img_dir.
        """
        logger.info(f"Extracting text from: {pdf_path}")
        return pymupdf4llm.to_markdown(
            pdf_path,
            page_chunks=True,
            write_images=True,
            image_path=img_dir,
            image_format="png",
        )

    def clean(self, text: str) -> str:
        """
        Removes pymupdf4llm artifacts from extracted text:
        - Image placeholder comments  (==> picture omitted <==)
        - Picture text blocks         (----- Start/End of picture text -----)
        - Spaced barcode sequences    (9 7 8 1 0 9 8 ...)
        """
        # Remove image placeholder comments
        text = re.sub(r'\*\*==>.*?<==\*\*', '', text)

        # Remove picture text blocks
        text = re.sub(
            r'\*\*----- Start of picture text -----\*\*'
            r'.*?'
            r'\*\*----- End of picture text -----\*\*',
            '',
            text,
            flags=re.DOTALL,
        )

        # Remove spaced barcode digit sequences e.g. "9 7 8 1 0 9 8..."
        text = re.sub(r'\b(\d\s){4,}\d\b', '', text)

        return text.strip()