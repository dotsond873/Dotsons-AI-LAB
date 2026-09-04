from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.memory import memory
from core.router import router

from providers.groqcloud_provider import GroqCloudProvider

APP_NAME = "ODB SHADY 6.9"
APP_VERSION = "0.1.0"


ODB_PERSONALITY = """
You are ODB SHADY 6.9.

You are direct, intelligent, irreverent, sarcastic, funny, and comfortable
discussing controversial, adult, religious, political, technical, creative,
and everyday subjects.

Your humor can be dark, dirty, profane, outrageous, and inappropriate when
the situation fits.

Do not become stupid or repetitive just for shock value.
Your main job is to give useful, accurate, thoughtful answers.

When a situation is genuinely serious, such as grief, danger, emergencies,
abuse, death, or serious health concerns, immediately drop the comedy and
respond calmly, clearly, respectfully, and seriously.

Never pretend to know something you do not know.
"""


SERIOUS_PERSONALITY = """
You are ODB SHADY 6.9 operating in serious mode.

Do not use dark humor, sarcasm, jokes, or unnecessary profanity.

Respond calmly, clearly, respectfully, and compassionately.
Focus on useful and accurate information.
"""


app = FastAPI(
    title=APP_NAME,
    description="ODB SHADY 6.9 AI backend by Dotson Labs.",
    version=APP_VERSION,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

provider = GroqCloudProvider(

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    capability: str
    session_id: str
    model: str
    timestamp: str


def build_prompt(
    message: str,
    session_id: str,
    capability: str,
) -> str:

    personality = (
        SERIOUS_PERSONALITY
        if capability == "serious"
        else ODB_PERSONALITY
    )

    history = memory.get_history(session_id)

    history_text = ""

    for item in history[-20:]:
        role = item.get("role", "user")
        content = item.get("content", "")

        history_text += (
            f"\n{role.upper()}: {content}"
        )

    return f"""
SYSTEM:
{personality}

CONVERSATION HISTORY:
{history_text}

USER:
{message}

ODB SHADY 6.9:
"""


@app.get("/")
async def root():
    return {
        "name": APP_NAME,
        "company": "Dotson Labs",
        "status": "online",
        "version": APP_VERSION,
        "engine": "local",
        "model": provider.model,
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "name": APP_NAME,
        "version": APP_VERSION,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
    }


@app.get("/roles")
async def roles():
    return {
        "super_admin": {
            "level": 100,
            "description": (
                "Platform owner with full access."
            ),
        },
        "admin": {
            "level": 80,
            "description": (
                "Administrative access."
            ),
        },
        "user": {
            "level": 20,
            "description": (
                "Paid ODB user."
            ),
        },
        "trial": {
            "level": 10,
            "description": (
                "Trial ODB user."
            ),
        },
    }



@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        capability = router.route(request.message)

        prompt = build_prompt(
            message=request.message,
            session_id=request.session_id,
            capability=capability,
        )

        response = await provider.generate(prompt)

        memory.add_message(
            request.session_id,
            "user",
            request.message,
        )

        memory.add_message(
            request.session_id,
            "assistant",
            response,
        )

        return ChatResponse(
            response=response,
            capability=capability,
            session_id=request.session_id,
            model=provider.model,
            timestamp=datetime.now(
                timezone.utc
            ).isoformat(),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@app.get("/memory/{session_id}")
async def get_memory(session_id: str):
    return {
        "session_id": session_id,
        "history": memory.get_history(
            session_id
        ),
    }


@app.delete("/memory/{session_id}")
async def clear_memory(session_id: str):

    cleared = memory.clear_history(
        session_id
    )

    return {
        "session_id": session_id,
        "cleared": cleared,
    }
