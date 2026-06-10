from pydantic import BaseModel, Field
from litellm import completion
from dotenv import load_dotenv
from prompts import COMPLETENESS_SYSTEM_PROMPT

MODEL = "gpt-4.1-nano"
load_dotenv(override=True)

class CompletenessResult(BaseModel):
    score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Coverage of important information available in the context. "
            "0 means most relevant information was omitted. "
            "1 means all important information relevant to the query "
            "was included in the answer."
        )
    )

    reasoning: str = Field(
        description="Explanation of the completeness assessment."
    )

def evaluate_completeness(query, chunks, answer):
    messages = [
        {"role": "system", "content": COMPLETENESS_SYSTEM_PROMPT},
        {"role": "user", "content": f"""
QUESTION

{query}

RETRIEVED CONTEXT

{chunks}

ANSWER

{answer}

Evaluate:

1. Identify important information in the context relevant to the question.
2. Determine whether the answer includes each important point.
3. Identify any important missing information.

Return your evaluation.
Provide a completeness score between 0 and 1, where 0 means most relevant information was omitted and 1 means all important information relevant to the query was included in the answer.
Also provide a brief explanation of your evaluation.""",
        },
    ]
    response = completion(model=MODEL, messages=messages, response_format=CompletenessResult)
    completeness_result = CompletenessResult.model_validate_json(response.choices[0].message.content)
    return completeness_result
