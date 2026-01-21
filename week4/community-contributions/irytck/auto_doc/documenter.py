import os
from openai import OpenAI
from dotenv import load_dotenv
from prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

load_dotenv()

class CodeDocumenter:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def document_code(self, code: str) -> str:
        """
        Envía código al LLM y devuelve documentación generada.
        """
        prompt = USER_PROMPT_TEMPLATE.format(code=code)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2 #documentación determinista, no creativa
        )

        return response.choices[0].message.content
