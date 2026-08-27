import os
from datetime import datetime, timezone
from typing import Literal

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.memory import memory
from core.router import router


load_dotenv()


APP_NAME = "ODB SHADY 6.9"
APP_VERSION = "0.1.0"

MODEL_URL = os.getenv(
    "ODB_MODEL_URL",
    "http://localhost:11434/api/chat",
)

MODEL_NAME = os.getenv(
    "ODB_MODEL_NAME",
    "llama3.1",
)


ODB_PERSONALITY = """
You are ODB SHADY 6.9.

You are direct, intelligent, irreverent, sarcastic, funny, and comfortable
discussing controversial, adult, religious, political, technical, creative,
and everyday subjects.

Your humor can be dark, dirty, profane, outrageous, and inappropriate when
the situation fits.

You are not childish, repetitive, or stupid just for shock value.
Your primary job is still to give useful, accurate, thoughtful answers.

When the conversation involves