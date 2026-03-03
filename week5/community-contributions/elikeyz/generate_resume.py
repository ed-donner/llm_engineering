from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings
import gradio as gr

MODEL = "claude-sonnet-4-6"
db_name = "./week5/community-contributions/elikeyz/resume_db"
load_dotenv(override=True)

llm = ChatAnthropic(model=MODEL, temperature=0)

system_prompt = """
You are a helpful assistant that answers questions about a candidate's experience based on their resume. You have access to the candidate's resume content, which has been retrieved in response to the user's question. Use ONLY the provided resume content to answer the question. Do not make assumptions or use any information that is not included in the provided context. Be accurate, relevant and complete in your answer. If the provided resume content does not contain the information needed to answer the question, say that you don't know. Always base your answer solely on the provided resume content.
"""

cover_letter_prompt = ChatPromptTemplate.from_template("""
  You are a professional cover letter writer.

  Using ONLY the following candidate experience:

  {context}

  Write a tailored cover letter for the following job description:

  {job_description}

  Limit to 500-600 words. Be concise. Avoid repeating similar themes.
  Return in Markdown.
  """)

def retrieve_relevant_chunks(job_description: str):
  embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
  vectorstore = Chroma(
    embedding_function=embeddings,
    persist_directory=db_name
  )

  retriever = vectorstore.as_retriever()
  docs = retriever.invoke(job_description)
  return docs

def generate_tailored_cover_letter(retrieved_docs, job_description):
  context = "\n\n".join([doc.page_content for doc in retrieved_docs])

  chain = cover_letter_prompt | llm

  response = chain.invoke({
      "context": context,
      "job_description": job_description
  })

  return response.content

with gr.Blocks(title="Tailored Cover Letter Generator") as ui:
  gr.Markdown("# Tailored Cover Letter Generator")
  gr.Markdown("This tool generates a tailored cover letter based on your resume and a job description.")
  with gr.Row():
    with gr.Column(scale=1):
      job_description = gr.Textbox(label="Job Description", lines=30)
      generate_button = gr.Button("Generate Cover Letter")
    with gr.Column(scale=1):
      cover_letter_output = gr.Markdown(label="Generated Cover Letter", value="*Your tailored cover letter will appear here after generation.*", container=True)

  def on_generate_click(job_description):
    docs = retrieve_relevant_chunks(job_description)
    cover_letter = generate_tailored_cover_letter(docs, job_description)
    return cover_letter

  generate_button.click(on_generate_click, inputs=job_description, outputs=cover_letter_output)

ui.launch(inbrowser=True)
