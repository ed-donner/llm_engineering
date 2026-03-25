"""
agents/summariser.py
Agent 3: Match Summariser (Frontier Model via OpenRouter)
Takes the CV, job preferences, and a matched job listing, then uses
a frontier LLM to produce a concise, personalised explanation of why
this job is a good fit and what the candidate should highlight.

Model: mistralai/mistral-7b-instruct (cheap, fast, good at structured tasks)
Fallback: openai/gpt-3.5-turbo
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are a career advisor helping job seekers understand 
why a specific job is a good match for them. Be concise, specific, and 
encouraging. Always ground your analysis in the actual CV and job details provided."""

MODEL = "mistralai/mistral-7b-instruct:free"


class Summariser:
    """Generates personalised match explanations via OpenRouter LLM."""

    def __init__( self ):
        self._model = MODEL
        self._client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

    def summarise_match(self, cv_text: str, preferences: str, job: dict) -> str:
        """
        Generate a personalised match explanation for a job listing.

        Returns a 3-4 sentence string explaining:
        1. Why this job fits the candidate
        2. Which specific skills/experience align
        3. One tip for the application
        """
        user_prompt = f"""A job seeker has been matched with a job listing. 
Provide a concise 3-4 sentence explanation of why this is a good match.

--- CANDIDATE CV ---
{cv_text[:1500]}

--- JOB PREFERENCES ---
{preferences or "No specific preferences provided."}

--- JOB LISTING ---
Title   : {job['title']}
Company : {job['company']}
Description:
{job['description'][:1500]}

Respond with:
1. Why this job fits their profile (1-2 sentences)
2. Their strongest matching skill or experience (1 sentence)  
3. One specific application tip (1 sentence)

Keep the total response under 100 words. Be direct and specific."""

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=200,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[Summariser] OpenRouter error: {e}")
            return (
                f"This {job['title']} role at {job['company']} aligns well with your profile. "
                f"Your background matches key requirements in the job description. "
                f"Highlight your most relevant experience in your cover letter."
            )
