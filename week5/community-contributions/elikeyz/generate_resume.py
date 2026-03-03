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

JOB_DESCRIPTION = """
About the job
Join the team redefining the future of global living.

At The Flex, we believe renting a home should feel instant, intelligent, and effortless — as seamless as booking a ride.

Our ambition is bold: enabling anyone to live anywhere, anytime, without friction.

Powered by Base360.ai, our proprietary automation engine, we’re building the operating system for modern renting — connecting property data, orchestrating operations, and enabling seamless stays across continents.

If you’re motivated by complex systems, automation, and building software that operates in the real world, this role gives you the ownership and scope to make a visible, lasting impact.

💡 What You’ll Build

As a Senior Software Engineer, you’ll design, build, and scale critical parts of The Flex platform — from core services and APIs to automation workflows and real-time systems.

You’ll operate with high autonomy, owning problems end-to-end and contributing directly to architectural decisions, while staying deeply hands-on with production code.

This role is for engineers who want impact, not meetings — and who take pride in building systems that are reliable, elegant, and scalable.

⚙️ Your Mission

Build Core Systems

Develop and maintain scalable services that power bookings, payments, availability, pricing, and guest experience.

Design Robust APIs

Create clean, well-structured APIs that connect Base360.ai with internal tools and external partners.

Automate Operations

Build event-driven workflows that eliminate manual processes and unlock operational leverage.

Ship with Confidence

Deploy and operate cloud-native infrastructure on AWS with a focus on reliability, security, and performance.

Solve Meaningful Problems

Work on real-time booking synchronization, pricing intelligence, keyless access logic, AI-powered alerts, and live operational dashboards.

Collaborate for Impact

Work closely with product, data, and operations teams to turn complex requirements into simple, effective systems.

🧠 You’re a Great Fit If You Have

Strong experience building production systems with Node.js, React, and AWS
A solid understanding of distributed systems and API-first design
Experience with Python / FastAPI for automation or data services (bonus)
A track record of shipping clean, maintainable, scalable code
Comfort owning features and systems from design to production
Curiosity about automation, AI-driven operations, and proptech
A bias toward execution — you deliver, iterate, and improve continuously

🌍 Why You’ll Love Working Here

Visible Impact

Your work will directly affect thousands of stays and real-world operations.

Autonomy & Trust

You’ll own systems and decisions without unnecessary process or micromanagement.

Fast Growth Environment

We move quickly, learn constantly, and value technical excellence.

Performance-Based Rewards

Competitive compensation with upside for high performers.

Remote-First

Work from anywhere — outcomes matter more than hours.

🚫 This Role Is Not for You If

You want a narrowly scoped role with limited ownership
You avoid production responsibility
You’re uncomfortable working in fast-moving environments
“Good enough” is your standard
"""

system_prompt = """
You are a helpful assistant that answers questions about a candidate's experience based on their resume. You have access to the candidate's resume content, which has been retrieved in response to the user's question. Use ONLY the provided resume content to answer the question. Do not make assumptions or use any information that is not included in the provided context. Be accurate, relevant and complete in your answer. If the provided resume content does not contain the information needed to answer the question, say that you don't know. Always base your answer solely on the provided resume content.
"""

cover_letter_prompt = ChatPromptTemplate.from_template("""
  You are a professional cover letter writer.

  Using ONLY the following candidate experience:

  {context}

  Rewrite the resume to align with this job:

  {job_description}

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
  print(docs)
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
      job_desc_input = gr.Textbox(label="Job Description", value=JOB_DESCRIPTION, lines=15)
      generate_button = gr.Button("Generate Cover Letter")
    with gr.Column(scale=1):
      cover_letter_output = gr.Markdown(label="Generated Cover Letter", value="*Your tailored cover letter will appear here after generation.*", container=True)

  def on_generate_click(job_description):
    docs = retrieve_relevant_chunks(job_description)
    cover_letter = generate_tailored_cover_letter(docs, job_description)
    return cover_letter

  generate_button.click(on_generate_click, inputs=job_desc_input, outputs=cover_letter_output)

ui.launch(inbrowser=True)
