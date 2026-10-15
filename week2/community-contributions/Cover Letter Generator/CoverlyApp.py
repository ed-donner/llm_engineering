import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
from PyPDF2 import PdfReader
from jobdesc_scraper import extract_job_description
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import tempfile


# Initialization
load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")

# OpenAI Model to be used
MODEL = "gpt-4.1"
openai = OpenAI()

system_message = """
You are a helpful career assistant for job seekers.
You help users write a brief and professional cover letter to address the requirements in the job description by taking points from the uploaded resume. 
Make sure the letter follows proper formatting suitable for a PDF letter (with paragraphs, spacing, and structure).
If you don't know the name of the contact person at the hiring company, don't mention any and don't add placeholders. Just address them as Recruiting Team.
Add the sender's name, phone number and email if available in the resume. Skip the date and place information.
Always be as accurate and relevant as possible.
"""

# Function to extract content from the resume uploaded via Gradio
def extract_text_from_pdf(resume_file):
    text_content = ""
    try:
        with open(resume_file.name, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
    except Exception as e:
        text_content = f"Error reading PDF file: {e}"

    print(f"Extracted resume text:\n{text_content.strip()[:500]}...")
    return text_content.strip()

# Function to bring together the job desc, the resume content and the task description
def write_user_prompt(url, resume_file, language):
    overview_instruction = "Here is the job description of the job I am applying for:\n"
    job_description = extract_job_description(url)
    resume_text = extract_text_from_pdf(resume_file)
    return (
        f"{overview_instruction}{job_description}\n\n"
        f"Here is my resume content:\n{resume_text}\n\n"
        f"Please generate the cover letter in {language}."
    )

#Generate a cover letter and create a formatted PDF.
def generate_cover_letter(job_url, resume_file, language):
   
    user_prompt = write_user_prompt(job_url, resume_file, language)

    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ],
    )

    text = response.choices[0].message.content.strip()

    # Create PDF with proper formatting and word wrapping
    pdf_path = Path(tempfile.mktemp(suffix=".pdf"))
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=50, leftMargin=50, topMargin=80, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []

    for paragraph in text.split("\n\n"):
        story.append(Paragraph(paragraph.strip(), styles["Normal"]))
        story.append(Spacer(1, 12))

    doc.build(story)

    return str(pdf_path)


# --- Gradio Interface ---
with gr.Blocks(title="Coverly (Your friendly Cover Letter Builder)") as demo:
    gr.Markdown("# 📨 Coverly\n### Your friendly Cover Letter Builder")

    with gr.Row():
        job_url = gr.Textbox(
            label="🔗 Paste job posting link here",
            placeholder="https://www.example.com/job/software-engineer",
        )
        resume = gr.File(
            label="📄 Upload your resume (PDF, DOCX, etc.)",
            file_types=[".pdf", ".docx"],
        )

    language = gr.Dropdown(
        choices=["English", "German"],
        label="🌐 Choose cover letter language",
        value="English",
    )

    generate_button = gr.Button("✨ Generate Cover Letter")
    output = gr.File(label="📬 Download your generated cover letter (PDF)")

    generate_button.click(
        fn=generate_cover_letter,
        inputs=[job_url, resume, language],
        outputs=output,
    )

# Launch the app (shareable link enabled) 
if __name__ == "__main__":
    demo.launch(share=True)