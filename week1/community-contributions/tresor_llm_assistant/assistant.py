# -*- coding:utf-8 -*-

from openai import OpenAI
from prompts import SYSTEM_PROMPTS

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)


class LLMAssistant:
    def __init__(self, model: str = "llama3.2"):
        self.model = model

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

    # ===========================
    # ======= Core Features =====
    # ===========================

    def summarize(self, text: str):
        return self._call(SYSTEM_PROMPTS["summarize"], f"Summarize:\n\n{text}")

    def classify(self, text: str):
        return self._call(
            SYSTEM_PROMPTS["classify"],
            f"Classify into Email, News, Announcement, Other:\n\n{text}"
        )

    def translate(self, text: str, language: str):
        return self._call(
            SYSTEM_PROMPTS["translate"],
            f"Translate into {language}:\n\n{text}"
        )

    def rewrite(self, text: str, style: str = "professional"):
        return self._call(
            SYSTEM_PROMPTS["rewrite"],
            f"Rewrite in {style} tone:\n\n{text}"
        )

    def extract_json(self, text: str):
        return self._call(
            SYSTEM_PROMPTS["json"],
            f"Extract structured JSON:\n\n{text}"
        )

    def generate_reply(self, text: str):
        return self._call(
            SYSTEM_PROMPTS["reply"],
            f"Write a reply:\n\n{text}"
        )

    def convert_to_bullets(self, text: str):
        return self._call(
            SYSTEM_PROMPTS["bullets"],
            f"Convert to bullet points:\n\n{text}"
        )

    def analyze(self, text: str):
        return self._call(
            SYSTEM_PROMPTS["analysis"],
            f"""
                Perform:
                1. Summary
                2. Key insights
                3. Important entities

                Text:
                {text}
            """
        )

    def sentiment_analysis(self, text: str):
        return self._call(
            SYSTEM_PROMPTS["sentiment"],
            f"""
                Analyze sentiment.

                Return:
                - Sentiment
                - Confidence
                - Explanation

                Text:
                {text}
            """
        )

    def sql_generation(self, description: str):
        return self._call(
            SYSTEM_PROMPTS["sql"],
            f"Convert to SQL:\n\n{description}\n\nReturn only SQL."
        )

    def meeting_minutes(self, transcript: str):
        return self._call(
            SYSTEM_PROMPTS["meeting"],
            f"""
                Extract meeting minutes:

                - Summary
                - Decisions
                - Action items
                - Participants

                Transcript:
                {transcript}
            """
        )

    def entity_extraction(self, text: str):
        return self._call(
            SYSTEM_PROMPTS["entities"],
            f"""
                Extract entities:

                - People
                - Organizations
                - Locations
                - Dates

                Text:
                {text}
            """
        )