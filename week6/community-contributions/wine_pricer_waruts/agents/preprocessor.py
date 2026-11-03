import os
import re
from litellm import completion
from pricer.batch import SYSTEM_PROMPT

DEFAULT_MODEL_NAME = "groq/openai/gpt-oss-20b"
DEFAULT_REASONING_EFFORT = "low"


class Preprocessor:
    """
    Rewrites any description of a wine into the summary format that our models were trained on
    """

    def __init__(self, model_name=None, reasoning_effort=DEFAULT_REASONING_EFFORT):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0
        self.model_name = model_name or os.getenv("PRICER_PREPROCESSOR_MODEL", DEFAULT_MODEL_NAME)
        self.reasoning_effort = reasoning_effort

    def messages_for(self, text: str) -> list[dict]:
        return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}]

    def preprocess(self, text: str) -> str:
        messages = self.messages_for(text)
        response = completion(
            messages=messages, model=self.model_name, reasoning_effort=self.reasoning_effort
        )
        self.total_input_tokens += response.usage.prompt_tokens
        self.total_output_tokens += response.usage.completion_tokens
        self.total_cost += response._hidden_params["response_cost"] or 0
        summary = response.choices[0].message.content
        lines = [line.strip() for line in summary.split("\n") if line.strip()]
        return "\n".join(self.tidy(line) for line in lines)

    @staticmethod
    def tidy(line: str) -> str:
        """
        The training summaries say "Points: 91", so reduce "Points: 91 points" or "Points: 91/100" to that
        """
        match = re.match(r"Points:\s*(\d+)", line)
        return f"Points: {match.group(1)}" if match else line
