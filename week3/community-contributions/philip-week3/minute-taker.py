import os
import json
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from openai import OpenAI

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

load_dotenv()

# Use OpenRouter as base_url
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio with OpenAI Whisper."""
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",  
            file=audio_file
        )
    return transcript.text

    
SYSTEM_PROMPT = """
You are a professional AI meeting assistant.

From the transcript generate structured meeting minutes in JSON:

- meeting_title
- date
- participants
- summary
- key_points
- decisions_made
- action_items (task, owner, deadline)
"""

def generate_minutes(transcript: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",  # OpenRouter model
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": transcript}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)



def export_to_pdf(minutes: dict, filename="meeting_minutes.pdf"):
    doc = SimpleDocTemplate(filename)
    elements = []
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]

    elements.append(Paragraph(f"<b>Meeting Title:</b> {minutes.get('meeting_title')}", normal_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(f"<b>Date:</b> {minutes.get('date')}", normal_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Summary:</b>", normal_style))
    elements.append(Paragraph(minutes.get("summary",""), normal_style))
    elements.append(Spacer(1,0.3*inch))
    elements.append(Paragraph("<b>Key Points:</b>", normal_style))
    for point in minutes.get("key_points",[]):
        elements.append(Paragraph(f"- {point}", normal_style))
    elements.append(Spacer(1,0.3*inch))
    elements.append(Paragraph("<b>Decisions:</b>", normal_style))
    for decision in minutes.get("decisions_made", []):
        elements.append(Paragraph(f"- {decision}", normal_style))
    elements.append(Spacer(1,0.3*inch))
    elements.append(Paragraph("<b>Action Items:</b>", normal_style))
    for action in minutes.get("action_items", []):
        elements.append(Paragraph(f"- Task: {action.get('task')} | Owner: {action.get('owner')} | Deadline: {action.get('deadline')}", normal_style))

    doc.build(elements)
    return filename

def send_email_with_attachment(to_email, subject, body, attachment_path):
    msg = EmailMessage()
    msg["From"] = os.getenv("EMAIL_ADDRESS")
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    with open(attachment_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=os.path.basename(attachment_path))

    with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as server:
        server.starttls()
        server.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
        server.send_message(msg)

