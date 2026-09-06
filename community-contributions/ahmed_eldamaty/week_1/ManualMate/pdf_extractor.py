import pymupdf

def extract_text(pdf_path):
    
  doc = pymupdf.open(pdf_path)

  all_text = ""
  for page in doc:
      all_text += page.get_text() + "\n"  # type: ignore

  doc.close()
  return all_text
