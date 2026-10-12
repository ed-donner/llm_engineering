"""
Streaming chat backend for a real ChatGPT-style UI.

Exposes POST /chat which streams tokens as Server-Sent Events (SSE).
Supports either OpenAI or Anthropic as the model provider, chosen per-request.

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000
"""

import json
import os
from typing import List, Literal

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Chat Backend")

# Allow your Next.js dev server (and prod origin) to call this API.
FRONTEND_ORIGINS = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    provider: Literal["openai", "anthropic"] = "openai"
    model: str | None = None


def sse(data: dict) -> str:
    """Format one Server-Sent Event line."""
    return f"data: {json.dumps(data)}\n\n"


async def stream_openai(messages: List[Message], model: str | None):
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    model = model or "gpt-4.1-mini"

    stream = client.chat.completions.create(
        model=model,
        messages=[m.model_dump() for m in messages],
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield sse({"type": "token", "text": delta})
    yield sse({"type": "done"})


async def stream_anthropic(messages: List[Message], model: str | None):
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    model = model or "claude-sonnet-4-6"

    # Anthropic wants system prompt separated out, not inline in messages.
    system_prompt = "\n".join(m.content for m in messages if m.role == "system") or None
    convo = [m.model_dump() for m in messages if m.role != "system"]

    with client.messages.stream(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=convo,
    ) as stream:
        for text in stream.text_stream:
            yield sse({"type": "token", "text": text})
    yield sse({"type": "done"})


@app.post("/chat")
async def chat(req: ChatRequest):
    generator = (
        stream_openai(req.messages, req.model)
        if req.provider == "openai"
        else stream_anthropic(req.messages, req.model)
    )
    return StreamingResponse(generator, media_type="text/event-stream")


@app.get("/health")
async def health():
    return {"status": "ok"}