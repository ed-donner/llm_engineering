from openai import OpenAI
from config import OPENROUTER_BASE, OPENROUTER_API_KEY, MODEL_INSIGHT

client = OpenAI(base_url=OPENROUTER_BASE, api_key=OPENROUTER_API_KEY)


def generate_insight(title, summary, context):

    prompt = f"""
Paper:
{title}

Summary:
{summary}

Similar work:
{context}

Explain:
1. Main contribution
2. Why it is interesting
3. Potential real world applications
"""

    response = client.chat.completions.create(
        model=MODEL_INSIGHT,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content