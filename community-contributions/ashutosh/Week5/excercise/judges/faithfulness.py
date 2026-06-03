from pydantic import BaseModel, Field
from litellm import completion
from dotenv import load_dotenv
from prompts import FAITHFULNESS_SYSTEM_PROMPT

MODEL = "gpt-4.1-nano"
load_dotenv(override=True)

class FaithfulnessResult(BaseModel):
    score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Faithfulness score between 0 and 1. "
            "0 means the answer is completely unsupported or contradicted by the context. "
            "1 means every factual claim in the answer is supported by the context."
        ),
    )

    reasoning: str = Field(
        description="Explanation of how the score was determined."
    )

def evaluate_faithfulness(chunks, answer):
    messages = [
        {"role": "system", "content": FAITHFULNESS_SYSTEM_PROMPT},
        {"role": "user", "content": f"""
RETRIEVED CONTEXT:

{chunks}

ANSWER:

{answer}

Evaluate:

1. Extract factual claims from the answer.
2. Determine whether each claim is supported by the context.
3. Identify unsupported or contradicted claims.

Return your evaluation.
Provide a faithfulness score between 0 and 1, where 0 means the answer is completely unsupported or contradicted by the context and 1 means every factual claim in the answer is supported by the context. 
Also provide a brief explanation of your evaluation.""",
        },
    ]
    response = completion(model=MODEL, messages=messages, response_format=FaithfulnessResult)
    faithfulness_result = FaithfulnessResult.model_validate_json(response.choices[0].message.content)
    return faithfulness_result
