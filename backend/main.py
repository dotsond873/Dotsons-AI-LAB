from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(
    title="Dotson Super AI",
    description="Core backend for the Dotson Labs modular AI platform.",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    timestamp: str


@app.get("/")
def root():
    return {
        "name": "Dotson Super AI",
        "company": "Dotson Labs",
        "status": "online",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    return ChatResponse(
        response=f"Dotson Super AI received: {request.message}",
        timestamp=datetime.utcnow().isoformat(),
    )
