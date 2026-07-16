import pytesseract
from PIL import Image
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract" # if tesseract not found

def extract_text(image_path) :
    try :
        img = Image.open(image_path).convert("L")
        text = pytesseract.image_to_string(img)
        return text
    
    except Exception as e :
        return f"[ERROR] ocr failed : {e}"