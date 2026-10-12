import os
from openai import OpenAI

from app.schemas.chat import Message
from app.utils.sse import sse


async def stream_openai(
    messages: list[Message],
    model: str | None = None,
):
    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"]
    )

    model = model or "gpt-4.1-mini"

    stream = client.chat.completions.create(
        model=model,
        messages=[m.model_dump() for m in messages],
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content

        if delta:
            yield sse({
                "type": "token",
                "text": delta,
            })

    yield sse({"type": "done"})