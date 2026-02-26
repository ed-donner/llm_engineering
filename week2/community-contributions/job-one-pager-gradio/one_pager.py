"""
Job posting → one-pager: turn a job ad into a structured one-pager for applications.
Supports URL (scrape) or pasted text (e.g. from LinkedIn). Uses OpenRouter.
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

from scraper import fetch_website_contents

load_dotenv(override=True)

DEFAULT_MODEL = "openai/gpt-4o-mini"

SYSTEM_PROMPT = """You are a career coach helping a candidate prepare their application.
Given a job posting (full text or excerpt), produce a clear, actionable one-pager in markdown.

Output exactly these sections with these headers. Use bullet points where indicated. Be concise.

## Role summary
2–3 sentences: what the role is, level, and main focus.

## Key requirements
Bullet list of must-have qualifications, skills, or experience from the posting.

## Nice-to-haves
Bullet list of preferred but not mandatory items.

## Suggested cover letter bullets
3–5 short bullet points the candidate could use in a cover letter or "Why I'm a fit" section. Each should tie their experience to the role. Write in first person, ready to paste or lightly edit.

## Keywords to include in resume
Comma-separated list of terms from the posting that should appear on the candidate's resume (skills, tools, methodologies).

Do not wrap the response in a code block. Output only the markdown."""

USER_PROMPT_PREFIX = """Here is the job posting text:

"""


def get_job_text(url_or_text: str) -> str:
    """If url_or_text looks like a URL, fetch and return page content. Otherwise return as-is."""
    s = url_or_text.strip()
    if s.startswith("http://") or s.startswith("https://"):
        return fetch_website_contents(s)
    return s


def generate_one_pager(
    url_or_pasted_text: str,
    *,
    model: str = DEFAULT_MODEL,
) -> str:
    """Generate a one-pager from a job URL or pasted job text. Uses OpenRouter."""
    job_text = get_job_text(url_or_pasted_text)
    if not job_text or len(job_text.strip()) < 50:
        return "Error: No meaningful job text. Provide a URL or paste the full job description (at least a few sentences)."

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_PREFIX + job_text},
    ]
    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content or ""


def stream_one_pager(
    url_or_pasted_text: str,
    *,
    model: str = DEFAULT_MODEL,
):
    """Stream the one-pager token-by-token. Yields text chunks."""
    job_text = get_job_text(url_or_pasted_text)
    if not job_text or len(job_text.strip()) < 50:
        yield "Error: No meaningful job text. Provide a URL or paste the full job description."
        return

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_PREFIX + job_text},
    ]
    stream = client.chat.completions.create(
        model=model, messages=messages, stream=True
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
