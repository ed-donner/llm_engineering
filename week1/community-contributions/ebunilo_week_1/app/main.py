"""FastAPI app for the company brochure generator (Day 5 business solution)."""
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from brochure import create_brochure

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Brochure generation will fail.")
    yield
    # shutdown if needed
    pass


app = FastAPI(
    title="Company Brochure Generator",
    description="Generate a brochure for a company from its website (Week 1 Day 5).",
    version="1.0.0",
    lifespan=lifespan,
)


class BrochureRequest(BaseModel):
    company_name: str
    url: str  # HttpUrl coerces to str; use str for simplicity with any URL

    model_config = {"json_schema_extra": {"example": {"company_name": "Hugging Face", "url": "https://huggingface.co"}}}


class BrochureResponse(BaseModel):
    brochure: str


@app.get("/health")
def health():
    """Liveness/readiness for containers and load balancers."""
    return {"status": "ok"}


@app.post("/brochure", response_model=BrochureResponse)
def generate_brochure(req: BrochureRequest):
    """Generate a markdown brochure for the given company and website URL."""
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured")
    try:
        brochure = create_brochure(req.company_name, req.url)
        return BrochureResponse(brochure=brochure)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
