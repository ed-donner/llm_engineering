from litellm import completion
from agents.agent import Agent
from pydantic import BaseModel, Field
from typing import List


class GrammarEvaluation(BaseModel):
    mistakes: List[str] = Field(description="List of grammar mistakes found")
    corrections: List[str] = Field(description="Corrected versions of the mistakes")
    explanation: str = Field(description="Explanation of the grammar issues")
    grammar_score: float = Field(description="Grammar score from 0 to 100")


class GrammarAgent(Agent):
    """
    Checks grammar correctness using LLM.
    """

    MODEL = "groq/openai/gpt-oss-20b"

    def __init__(self):
        self.name = "GrammarAgent"
        self.color = Agent.YELLOW
        self.log("GrammarAgent initialized")

    def evaluate(self, sentence: str) -> GrammarEvaluation:

        prompt = f"""
Evaluate the grammar of the following sentence:

{sentence}

Return the result using the specified schema.
"""

        response = completion(
            model=self.MODEL,
            reasoning_effort="low",
            messages=[{"role": "user", "content": prompt}],
            response_format=GrammarEvaluation  #forces schema
        )

        result = response.choices[0].message.content

        # parse into Pydantic model
        return GrammarEvaluation.model_validate_json(result)