import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")
    
    return OpenAI(api_key=api_key)


def explain(query, docs):
    client = get_client()

    print(" Explain is called ")

    context = "\n\n".join(docs)

    prompt = f"""
    Explain how this column is derived based on received docs. Do not add any extra info:
    {query}

    Context:
    {context}
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    print(res.choices[0].message.content)

    return res.choices[0].message.content