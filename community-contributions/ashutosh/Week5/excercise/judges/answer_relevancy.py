from pydantic import BaseModel, Field
from litellm import completion
from dotenv import load_dotenv
from prompts import ANSWER_RELEVANCE_SYSTEM_PROMPT

MODEL = "gpt-4.1-nano"
load_dotenv(override=True)


class AnswerRelevanceResult(BaseModel):
    score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Answer relevance score between 0 and 1. "
            "Measures how well the answer addresses the user's query and intent. "
            "A score of 0.0 means the answer is completely unrelated to the query. "
            "A score of 1.0 means the answer directly, completely, and specifically addresses the user's query."
        ),
    )

    reasoning: str = Field(
        description=(
            "Explanation of the relevance assessment."
        )
    )

def evaluate_answer_relevance(query, answer):
    messages = [
        {"role": "system", "content": ANSWER_RELEVANCE_SYSTEM_PROMPT},
        {"role": "user", "content": f"""
QUESTION

{query}

ANSWER

{answer}

Evaluate:

1. What is the user's intent?
2. Does the answer address that intent?
3. Are there irrelevant sections?

Return your evaluation.
Provide a relevance score between 0 and 1, where 0 means the answer is completely unrelated to the query and 1 means the answer directly, completely, and specifically addresses the user's query.
Also provide a brief explanation of your evaluation."""
        },
    ]
    response = completion(model=MODEL, messages=messages, response_format=AnswerRelevanceResult)
    answer_relevance_result = AnswerRelevanceResult.model_validate_json(response.choices[0].message.content)
    return answer_relevance_result
