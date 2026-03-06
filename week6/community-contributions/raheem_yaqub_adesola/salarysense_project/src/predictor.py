from openai import OpenAI
from src.config import MODEL_NAME

client = OpenAI()

def base_model_predict(prompt):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def fine_tuned_predict(prompt, ft_model):
    response = client.chat.completions.create(
        model=ft_model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
