import requests
from fpdf import FPDF
from website_summarizer import summarize


user_input = input("Please enter the WEB URL to summarize: ")
try:
    summary = summarize(user_input)
except requests.exceptions.RequestException:
    print(f"Error occurred while fetching the website: {user_input}."
          f" Please check the URL and try again.")

else:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()

    pdf.set_font("Arial", size=24)
    pdf.set_text_color(150, 100, 150)
    pdf.cell(0, 10, txt="website summarizer", ln=1, align="L")

    pdf.line(10, 21, 200, 21)

    pdf.set_font("Times", size=12)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 10, txt=summary, align="L")

    pdf.output("summary.pdf")