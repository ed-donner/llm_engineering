from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest
from app.services.openai_service import stream_openai

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(req: ChatRequest):
    generator = stream_openai(
        messages=req.messages,
        provider=req.provider,
        model=req.model,
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
    )