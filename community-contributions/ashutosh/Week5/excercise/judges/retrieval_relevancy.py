from pydantic import BaseModel, Field
from litellm import completion
from dotenv import load_dotenv
from prompts import RETRIEVAL_RELEVANCE_SYSTEM_PROMPT

MODEL = "gpt-4.1-nano"
load_dotenv(override=True)

class RetrievalRelevanceResult(BaseModel):
    score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Relevance of retrieved context to the user query. "
            "0 means the retrieved chunks are entirely irrelevant. "
            "1 means all retrieved chunks are highly relevant and useful "
            "for answering the query."
        )
    )

    reasoning: str = Field(
        description="Short explanation of the evaluation."
    )

def evaluate_retrieval_relevance(query, chunks):
    messages = [
        {"role": "system", "content": RETRIEVAL_RELEVANCE_SYSTEM_PROMPT},
        {"role": "user", "content": f"""
USER QUESTION

{query}

RETRIEVED CONTEXT

{chunks}

Evaluate:

1. How relevant are the retrieved chunks to answering the question?
2. Are there irrelevant chunks present?
3. Could a competent model answer the question using these chunks?

Return your evaluation. 
Provide a relevance score between 0 and 1, where 0 means the retrieved chunks are entirely irrelevant and 1 means all retrieved chunks are highly relevant and useful for answering the question. 
Also provide a brief explanation of your evaluation."""
        },
    ]
    response = completion(model=MODEL, messages=messages, response_format=RetrievalRelevanceResult)
    retrieval_relevance_result = RetrievalRelevanceResult.model_validate_json(response.choices[0].message.content)
    return retrieval_relevance_result
