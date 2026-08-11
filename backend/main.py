from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.router import router
from providers.openai_provider import OpenAIProvider
from providers.claude_provider import ClaudeProvider
from providers.gemini_provider import GeminiProvider
from providers.grok_provider import GrokProvider


app = FastAPI(
    title="Dotson Super AI",
    description="Core backend for the Dotson Labs modular AI platform.",
    version="0.2.0",
)


class ChatRequest(BaseModel):
    message: str
    provider: str | None = None


class ChatResponse(BaseModel):
    response: str
    provider: str
    capability: str
    timestamp: str


def get_provider(name: str):
    providers = {
        "openai": OpenAIProvider,
        "claude": ClaudeProvider,
        "gemini": GeminiProvider,
        "grok": GrokProvider,
    }

    provider_class = providers.get(name)

    if not provider_class:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {name}",
        )

    return provider_class()


def choose_provider(capability: str) -> str:
    provider_map = {
        "coding": "claude",
        "research": "grok",
        "image": "openai",
        "planning": "gemini",
        "general": "openai",
    }

    return provider_map.get(capability, "openai")


@app.get("/")
def root():
    return {
        "name": "Dotson Super AI",
        "company": "Dotson Labs",
        "status": "online",
        "version": "0.2.0",
        "providers": [
            "openai",
            "claude",
            "gemini",
            "grok",
        ],
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    capability = router.route(request.message)

    provider_name = request.provider or choose_provider(capability)

    provider = get_provider(provider_name)

    try:
        answer = await provider.generate(request.message)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"{provider_name} provider error: {str(exc)}",
        )

    return ChatResponse(
        response=answer,
        provider=provider_name,
        capability=capability,
        timestamp=datetime.utcnow().isoformat(),
    )
