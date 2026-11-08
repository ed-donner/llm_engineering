
from IPython.display import Markdown, display, update_display

def create_user_prompt(question):
    return question

def create_system_prompt():
    return (
        "You are a technical explainer. "
        "Reply in 50 words or fewer. Do not exceed 50 words. "
        "Use plain markdown, no headings."
    )

def create_chat_messages(question):
    return [
        {"role": "system", "content": create_system_prompt()},
        {"role": "user", "content": create_user_prompt(question)},
    ]

def respond(question, client, model, with_stream = False):
    messages = create_chat_messages(question)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=with_stream
    )

    if with_stream:
        response_text = ""
        display_handle = display(Markdown(""), display_id=True)
        for chunk in response:
            response_text += chunk.choices[0].delta.content or ''
            update_display(Markdown(response_text), display_id=display_handle.display_id)
    else:
        result = response.choices[0].message.content
        display(Markdown(result))
