import os
from typing import Optional
from pathlib import Path
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_core import documents
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import json
import re
import PyPDF2

load_dotenv(override=True)

anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

anthropic_url = "https://api.anthropic.com/v1/"

anthropic = OpenAI(api_key=anthropic_api_key, base_url=anthropic_url)
ANTHROPIC_MODEL = "claude-sonnet-4-6"

llm = ChatAnthropic(model=ANTHROPIC_MODEL, temperature=0)

class ContactInfo(BaseModel):
  full_name: str
  email: EmailStr
  phone: Optional[str] = ""
  location: Optional[str] = ""
  linkedin: Optional[str] = ""
  github: Optional[str] = ""
  website: Optional[str] = ""

class Experience(BaseModel):
  company: str
  title: str
  location: Optional[str] = ""
  start_date: Optional[str] = ""
  end_date: Optional[str] = ""
  bullets: List[str]

class Education(BaseModel):
  institution: str
  degree: str
  start_date: Optional[str] = ""
  end_date: Optional[str] = ""

class ResumeSchema(BaseModel):
  contact: ContactInfo
  headline: Optional[str] = ""
  summary: Optional[str] = ""
  experience: List[Experience]
  education: List[Education]
  skills: List[str]

def pdf_to_markdown(pdf_path: str, output_path: Optional[str] = None) -> str:
	"""
	Parses a PDF file and converts its text content to Markdown format for RAG chunking.
	Args:
		pdf_path (str): Path to the PDF file.
		output_path (Optional[str]): If provided, saves the Markdown to this file.
	Returns:
		str: The Markdown content as a string.
	"""
	pdf_path = Path(pdf_path)
	if not pdf_path.exists():
		raise FileNotFoundError(f"PDF file not found: {pdf_path}")

	reader = PyPDF2.PdfReader(str(pdf_path))
	md_lines = []
	for i, page in enumerate(reader.pages):
		text = page.extract_text()
		if text:
			# Simple conversion: treat each line as a Markdown paragraph
			for line in text.splitlines():
				line = line.strip()
				if line:
					md_lines.append(line)

	markdown_content = "\n\n".join(md_lines)
	refined_markdown = refine_markdown(markdown_content)

	if output_path:
		with open(output_path, "w", encoding="utf-8") as f:
			f.write(refined_markdown)
	return refined_markdown

def refine_markdown(md_content):
  system_prompt = "You are a helpful assistant that refines Markdown content for better readability and structure. Please improve the formatting, add appropriate headings, and ensure the content is well-organized ideally for chunking."

  user_prompt = f"Here is the Markdown content extracted from a PDF:\n\n{md_content}\n\nPlease refine this Markdown for better readability and structure."

  messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt}
  ]

  response = anthropic.chat.completions.create(
		model=ANTHROPIC_MODEL,
    messages=messages,
  )
  return response.choices[0].message.content

def parse_resume(resume_text: str):
  prompt = ChatPromptTemplate.from_template("""
  You are a resume parser.

  Convert the following resume into structured JSON.

  Rules:
  - Follow the schema strictly.
  - Infer missing section headers.
  - Group bullets under correct job.
  - Normalize date formats.
  - Return ONLY valid JSON.
  - Do not include explanations.

  Schema:
  {{
    "contact": {{
      "full_name": "",
      "email": "",
      "phone": "",
      "location": "",
      "linkedin": "",
      "github": "",
      "website": ""
    }},
    "headline": "",
    "summary": "",
    "experience": [{{
        "company": "",
        "title": "",
        "location": "",
        "start_date": "",
        "end_date": "",
        "bullets": []
    }}],
    "education": [{{
        "institution": "",
        "degree": "",
        "start_date": "",
        "end_date": ""
    }}],
    "skills": []
  }}

  --- RESUME ---
  {resume}
  """)

  chain = prompt | llm
  response = chain.invoke({"resume": resume_text})

  # Remove Markdown JSON code block wrapper if present
  raw = response.content.strip()
  # Remove triple backticks and optional 'json' label
  raw = re.sub(r"^```json\s*|^```|```$", "", raw, flags=re.MULTILINE).strip()

  try:
    parsed = json.loads(raw)
  except json.JSONDecodeError as e:
    raise ValueError(f"LLM did not return valid JSON. Raw response:\n{response.content}") from e

  return ResumeSchema(**parsed)

def create_chunks(resume: ResumeSchema):
  documents = []

  candidate_name = resume.contact.full_name if resume.contact and resume.contact.full_name else "Candidate"
  headline = resume.headline if resume.headline else ""
  location = resume.contact.location if resume.contact and resume.contact.location else ""
  email = resume.contact.email if resume.contact and resume.contact.email else ""
  linkedin = resume.contact.linkedin if resume.contact and resume.contact.linkedin else ""
  github = resume.contact.github if resume.contact and resume.contact.github else ""
  website = resume.contact.website if resume.contact and resume.contact.website else ""
  phone = resume.contact.phone if resume.contact and resume.contact.phone else ""

  # ------------- SUMMARY -------------
  if resume.summary:
    documents.append(
      Document(
        page_content=f"""
{candidate_name}
{headline}

Professional Summary:
{resume.summary}
""".strip(),
        metadata={
          "type": "summary",
          "candidate": candidate_name,
          "location": location,
          "headline": headline,
          "email": email,
          "linkedin": linkedin,
          "github": github,
          "website": website,
          "phone": phone
        }
      )
    )

  # ------------ EXPERIENCE -------------
  for job in resume.experience:
    text = f"""
{candidate_name} - {headline}

Role: {job.title}
Company: {job.company}
Location: {job.location}
Dates: {job.start_date} - {job.end_date}

Responsibilities and Achievements:
{' '.join(job.bullets)}
"""

    documents.append(
      Document(
        page_content=text.strip(),
        metadata={
          "type": "experience",
          "candidate": candidate_name,
          "email": email,
          "linkedin": linkedin,
          "github": github,
          "website": website,
          "phone": phone,
          "company": job.company,
          "title": job.title,
          "start_date": job.start_date,
          "end_date": job.end_date,
        }
      )
    )

  # ------------ EDUCATION -------------
  for edu in resume.education:
    text = f"""
{candidate_name}

Education:
{edu.degree}
Institution: {edu.institution}
Dates: {edu.start_date} - {edu.end_date}
"""

    documents.append(
      Document(
        page_content=text.strip(),
        metadata={
          "type": "education",
          "candidate": candidate_name,
          "institution": edu.institution,
          "email": email,
          "linkedin": linkedin,
          "github": github,
          "website": website,
          "phone": phone
        }
      )
    )

  # ----------- SKILLS -------------
  if resume.skills:
    documents.append(
      Document(
        page_content=f"""
{candidate_name} - Skills

{", ".join(resume.skills)}
""",
        metadata={
          "type": "skills",
          "candidate": candidate_name,
          "email": email,
          "linkedin": linkedin,
          "github": github,
          "website": website,
          "phone": phone
        }
      )
    )

  text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
  chunks = text_splitter.split_documents(documents)

  print (f"Created {len(chunks)} chunks from {len(documents)} sections of the resume.")

  return chunks

def store_chunks_in_db(chunks, db_name):
  embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

  if os.path.exists(db_name):
    Chroma(persist_directory=db_name, embedding_function=embeddings).delete_collection()

  vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=db_name
  )

  collection = vectorstore._collection
  count = collection.count()

  sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
  dimensions = len(sample_embedding)
  print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")

# Example usage
if __name__ == "__main__":
  pdf_file = "./week5/community-contributions/elikeyz/resume.pdf"  # Update this path to your PDF file
  md_output_file = "./week5/community-contributions/elikeyz/resume.md"  # Optional: specify output Markdown file
  db_name = "./week5/community-contributions/elikeyz/resume_db" # Update this path to your desired database directory

  print("Starting resume ingestion process...")
  markdown_content = pdf_to_markdown(pdf_file, md_output_file)
  print("PDF converted to Markdown successfully.")
  structured_resume = parse_resume(markdown_content)
  print("Resume parsed into structured format successfully.")
  chunks = create_chunks(structured_resume)
  print("Documents created from structured resume successfully.")
  store_chunks_in_db(chunks, db_name)
  print("Chunks stored in database successfully.")
