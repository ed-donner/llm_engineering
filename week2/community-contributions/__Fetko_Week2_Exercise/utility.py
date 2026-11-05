from openai import OpenAI
from torch import empty


def call_model_for_conversation(client, model, system_message, conversation):
    user_prompt = f"""
        You are Blake in a conversation with Alex and Charlie.

        Conversation so far:
        {conversation}

        Now respond as Blake.
    """

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.choices[0].message.content 
