import json
from typing import Any, Callable

from openai import OpenAI, pydantic_function_tool
from pydantic import BaseModel

# Registry: tool name -> (Pydantic model class, callable).
# Use registry_tools(registry) for the API and handle_tool_calls(message, registry) to run calls.
ToolRegistry = dict[str, tuple[type[BaseModel], Callable[..., Any]]]


def tool_descriptor(model: type[BaseModel], func: Callable[..., Any], *, description: str | None = None):
    """Create a tool descriptor for a tool function.

    The tool descriptor built using Pydantic model.
    
    Args:
        model: The Pydantic model class defining the tool's parameters.
        func: The function to use for the tool.
        description: The description of the tool.
    Returns:
        A tool descriptor for the tool function.
    """
    out = pydantic_function_tool(model, description=description or func.__doc__)
    out["function"]["name"] = func.__name__
    return out


def registry_tools(registry: ToolRegistry) -> list[dict[str, Any]]:
    """Build the list of tool descriptors for the chat API from a registry.

    Each entry is {"type": "function", "function": {...}} suitable for
    the `tools` argument of `client.chat.completions.create(...)`.

    Args:
        registry: Map of tool name -> (model class, callable).

    Returns:
        List of tool param dicts for the API.
    """
    return [
        tool_descriptor(model, func)
        for _name, (model, func) in registry.items()
    ]


def handle_tool_calls(message: Any, registry: ToolRegistry) -> list[dict[str, Any]]:
    """Execute tool calls from a message using the registry and return tool responses.

    For each tool call in the message, looks up (model, func) in the registry,
    validates arguments with the Pydantic model, calls the function, and collects
    responses in the format expected for the next API call (role="tool", content, tool_call_id).

    Args:
        message: Chat message with a `tool_calls` attribute (each item has
            .function.name, .function.arguments, .id).
        registry: Map of tool name -> (model class, callable).

    Returns:
        List of {"role": "tool", "content": str, "tool_call_id": str} dicts.
    """
    responses: list[dict[str, Any]] = []
    for tool_call in message.tool_calls:
        name = tool_call.function.name
        raw = tool_call.function.arguments or "{}"
        tool_call_id = tool_call.id

        if name not in registry:
            responses.append({
                "role": "tool",
                "content": f"Error: Tool {name} not found",
                "tool_call_id": tool_call_id,
            })
            continue

        model_cls, func = registry[name]
        try:
            arguments = json.loads(raw)
        except json.JSONDecodeError as e:
            responses.append({
                "role": "tool",
                "content": f"Error: Invalid JSON for tool {name}: {e}",
                "tool_call_id": tool_call_id,
            })
            continue

        try:
            params = model_cls.model_validate(arguments)
            result = func(**params.model_dump())
            responses.append({
                "role": "tool",
                "content": str(result),
                "tool_call_id": tool_call_id,
            })
        except Exception as e:
            responses.append({
                "role": "tool",
                "content": f"Error: {e}",
                "tool_call_id": tool_call_id,
            })

    return responses




def model_streaming(client: OpenAI, model: str, prompt: str, **kwargs):
    """Stream the response from the model.

    Args:
        model: The model to use for the streaming.
        prompts: list of prompts to use for the streaming.
        **kwargs: Additional arguments to pass to the model.
    Returns:
        A generator of the response from the model.
    """
    messages = [{"role": "user", "content": prompt}]
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        **kwargs
    )
    for chunk in stream:
        yield chunk


def model_completion(client: OpenAI, model: str, messages: str, **kwargs):
    """Complete the response from the model.

    Args:
        model: The model to use for the completion.
        prompts: The prompts to use for the completion.
        **kwargs: Additional arguments to pass to the model.
    Returns:
        The response from the model.
    """
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=False,
        **kwargs
    )
    return response

