from litellm import completion
from dotenv import load_dotenv
import os

load_dotenv(override=True)

DEFAULT_MODEL_NAME = os.getenv("SALARY_PREPROCESSOR_MODEL", "gpt-4o-mini")
DEFAULT_REASONING_EFFORT = "low" if "gpt-oss" in DEFAULT_MODEL_NAME else None

SYSTEM_PROMPT = """Create a concise description of a job listing. Respond only in this format. Do not include application instructions.
Title: Rewritten short precise job title
Category: eg Data Science, Software Engineering, DevOps
Company: Company name
Location: Location or Remote
Description: 1 sentence description of the role
Requirements: 1 sentence on key requirements"""


class Preprocessor:
    def __init__(
        self,
        model_name=DEFAULT_MODEL_NAME,
        reasoning_effort=DEFAULT_REASONING_EFFORT,
        base_url=None,
    ):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0
        self.model_name = model_name
        self.reasoning_effort = reasoning_effort
        self.base_url = base_url
        if "ollama" in model_name and not base_url:
            self.base_url = "http://localhost:11434"

    def messages_for(self, text: str) -> list[dict]:
        return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}]

    def preprocess(self, text: str) -> str:
        messages = self.messages_for(text)
        kwargs = dict(messages=messages, model=self.model_name)
        if self.reasoning_effort:
            kwargs["reasoning_effort"] = self.reasoning_effort
        if self.base_url:
            kwargs["api_base"] = self.base_url
        response = completion(**kwargs)
        self.total_input_tokens += response.usage.prompt_tokens
        self.total_output_tokens += response.usage.completion_tokens
        cost = getattr(response, "_hidden_params", {}).get("response_cost", 0)
        self.total_cost += cost or 0
        return response.choices[0].message.content
