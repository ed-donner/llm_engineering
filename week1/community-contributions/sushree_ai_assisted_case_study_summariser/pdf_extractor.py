import PyPDF2
#a=PyPDF2.PdfReader('sushree/CASE_STUDY_TATA_NANO.pdf')
#print(a.metadata)
#print('Number of Pages: ',len(a.pages))
#print(a.pages[2].extract_text())
#text=""
#for i in (len(a.pages)):
#    page_text=a.pages[i].extract_text()
#    if page_text:
#        text+=page_text

def extract_pdf_text(file_path):
    a=PyPDF2.PdfReader(file_path)
    text=""
    for i in range(len(a.pages)):
        page_text=a.pages[i].extract_text()
        if page_text:     #Handle pages where no text is there
            text+=page_text
    
    return text