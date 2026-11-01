import json

from tools import TOOLS, execute_tool


def chat_with_chef(
    user_message: str,
    client,
    model: str,
    system_prompt: str,
    history=None
):
    messages = [
        {"role": "system", "content": system_prompt},
        *(history or []),
        {"role": "user", "content": user_message}
    ]

    max_iterations = 10
    iterations = 0

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        reasoning_effort="none"
    )

    while (
        response.choices[0].finish_reason == "tool_calls"
        and iterations < max_iterations
    ):
        iterations += 1

        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        for tool_call in message.tool_calls or []:
            name = tool_call.function.name

            try:
                arguments = json.loads(tool_call.function.arguments)
                result = execute_tool(name, arguments)
            except (json.JSONDecodeError, TypeError, ValueError) as error:
                result = {"error": str(error)}

            print(f"Tool called: {name}")
            print(f"Arguments: {tool_call.function.arguments}")
            print(f"Result: {result}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice=(
                "none" if iterations >= max_iterations else "auto"
            ),
            reasoning_effort="none"
        )

    choice = response.choices[0]

    if choice.finish_reason != "stop":
        raise RuntimeError(
            f"Assistant did not finish successfully: "
            f"{choice.finish_reason}"
        )

    final_message = choice.message
    messages.append(final_message.model_dump(exclude_none=True))

    return final_message.content or "", messages[1:]



def respond(message, history, client, model, system_prompt):
    return chat_with_chef(
        user_message=message,
        client=client,
        model=model,
        system_prompt=system_prompt,
        history=history
    )



def add_user_message(message, chat_history):
    """Immediately display the user's message."""

    if not message or not message.strip():
        return "", chat_history

    updated_history = (chat_history or []) + [
        {"role": "user", "content": message}
    ]

    return "", updated_history



def generate_response(
    chat_history,
    state,
    client,
    model,
    system_prompt
):
    if not chat_history or chat_history[-1]["role"] != "user":
        return chat_history, state, None

    user_message = chat_history[-1]["content"]

    answer, updated_state = respond(
        user_message,
        state,
        client,
        model,
        system_prompt
    )

    # Detect recipe responses
    is_recipe = answer.lstrip().startswith("[RECIPE]")

    # Remove marker before displaying
    clean_answer = (
        answer.lstrip().removeprefix("[RECIPE]").strip()
        if is_recipe else answer
    )

    updated_history = chat_history + [
        {"role": "assistant", "content": clean_answer}
    ]

    # Pass the recipe to the image generator
    recipe = clean_answer if is_recipe else None

    return updated_history, updated_state, recipe


