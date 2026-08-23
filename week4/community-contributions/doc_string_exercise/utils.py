from enum import Enum
from pathlib import Path


class Model(Enum):
    """
    Enumeration of supported AI models.
    """
    OPENAI_MODEL = "gpt-4o"
    CLAUDE_MODEL = "claude-3-5-sonnet-20240620"


def get_system_message() -> str:
    """
    Generate a system message for AI assistants creating docstrings.

    :return: A string containing instructions for the AI assistant.
    :rtype: str
    """
    system_message = "You are an assistant that creates doc strings in reStructure Text format for an existing python function. "
    system_message += "Respond only with an updated python function; use comments sparingly and do not provide any explanation other than occasional comments. "
    system_message += "Be sure to include typing annotation for each function argument or key word argument and return object types."

    return system_message


def user_prompt_for(python: str) -> str:
    """
    Generate a user prompt for rewriting Python functions with docstrings.

    :param python: The Python code to be rewritten.
    :type python: str
    :return: A string containing the user prompt and the Python code.
    :rtype: str
    """
    user_prompt = "Rewrite this Python function with doc strings in the reStructuredText style."
    user_prompt += "Respond only with python code; do not explain your work other than a few comments. "
    user_prompt += "Be sure to write a description of the function purpose with typing for each argument and return\n\n"
    user_prompt += python
    return user_prompt


def messages_for(python: str, system_message: str) -> list:
    """
    Create a list of messages for the AI model.

    :param python: The Python code to be processed.
    :type python: str
    :param system_message: The system message for the AI assistant.
    :type system_message: str
    :return: A list of dictionaries containing role and content for each message.
    :rtype: list
    """
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt_for(python)}
    ]


def write_output(output: str, file_suffix: str, file_path: Path) -> None:
    """
    Write the processed output to a file.

    :param output: The processed Python code with docstrings.
    :type output: str
    :param file_suffix: The suffix to be added to the output file name.
    :type file_suffix: str
    :param file_path: The path of the input file.
    :type file_path: Path
    :return: None
    """
    code = output.replace("", "").replace("", "")
    out_file = file_path.with_name(f"{file_path.stem}{file_suffix if file_suffix else ''}.py")
    out_file.write_text(code)


def add_doc_string(client: object, system_message: str, file_path: Path, model: str) -> None:
    """
    Add docstrings to a Python file using the specified AI model.

    :param client: The AI client object.
    :type client: object
    :param system_message: The system message for the AI assistant.
    :type system_message: str
    :param file_path: The path of the input Python file.
    :type file_path: Path
    :param model: The AI model to be used.
    :type model: str
    :return: None
    """
    if 'gpt' in model:
        add_doc_string_gpt(client=client, system_message=system_message, file_path=file_path, model=model)
    else:
        add_doc_string_claude(client=client, system_message=system_message, file_path=file_path, model=model)


def add_doc_string_gpt(client: object, system_message: str, file_path: Path, model: str = 'gpt-4o') -> None:
    """
    Add docstrings to a Python file using GPT model.

    :param client: The OpenAI client object.
    :type client: object
    :param system_message: The system message for the AI assistant.
    :type system_message: str
    :param file_path: The path of the input Python file.
    :type file_path: Path
    :param model: The GPT model to be used, defaults to 'gpt-4o'.
    :type model: str
    :return: None
    """
    code_text = file_path.read_text(encoding='utf-8')
    stream = client.chat.completions.create(model=model, messages=messages_for(code_text, system_message), stream=True)
    reply = ""
    for chunk in stream:
        fragment = chunk.choices[0].delta.content or ""
        reply += fragment
        print(fragment, end='', flush=True)
    write_output(reply, file_suffix='_gpt', file_path=file_path)


def add_doc_string_claude(client: object, system_message: str, file_path: Path, model: str = 'claude-3-5-sonnet-20240620') -> None:
    """
    Add docstrings to a Python file using Claude model.

    :param client: The Anthropic client object.
    :type client: object
    :param system_message: The system message for the AI assistant.
    :type system_message: str
    :param file_path: The path of the input Python file.
    :type file_path: Path
    :param model: The Claude model to be used, defaults to 'claude-3-5-sonnet-20240620'.
    :type model: str
    :return: None
    """
    code_text = file_path.read_text(encoding='utf-8')
    result = client.messages.stream(
        model=model,
        max_tokens=2000,
        system=system_message,
        messages=[{"role": "user", "content": user_prompt_for(code_text)}],
    )
    reply = ""
    with result as stream:
        for text in stream.text_stream:
            reply += text
            print(text, end="", flush=True)
    write_output(reply, file_suffix='_claude', file_path=file_path)