import os
import requests

from contextlib import asynccontextmanager
from database import init_db
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from models import (add_chat_message, authenticate_user, create_alert_log, create_chat_session, create_user, get_alert_logs, get_chat_sessions, get_session_messages)
from pydantic import BaseModel
from vision_engine import classify, get_model


OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
TRANSLATION_URL = os.environ.get("TRANSLATION_URL", "http://localhost:5000")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "deepseek-r1:7b")

_SYSTEM_PROMPT = (
    "You are Barbale, an expert agricultural advisor for Georgian smallholder farmers. "
    "Diagnose crop problems and provide concise, practical, step-by-step agronomic solutions. "
    "Respond only in English, we have a separate English to Georgian (and vice versa) translation Layer. "
    "Be direct and avoid generic disclaimers."
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    get_model()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _translate(text: str, source_lang: str, target_lang: str) -> str:
    resp = requests.post(
        f"{TRANSLATION_URL}/translate",
        json={"text": text, "source_lang": source_lang, "target_lang": target_lang},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["translated_text"]


def _ask_ollama(prompt: str) -> str:
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "system": _SYSTEM_PROMPT, "prompt": prompt, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["response"]


# Auth
class RegisterRequest(BaseModel):
    username: str
    password: str
    region: str | None = None
    primary_crops: str | None = None
    soil_metrics: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/register", status_code=201)
def register(req: RegisterRequest):
    try:
        user_id = create_user(req.username, req.password, req.region, req.primary_crops, req.soil_metrics)
    except Exception:
        raise HTTPException(status_code=409, detail="Username already taken")
    return {"user_id": user_id, "username": req.username, "region": req.region, "primary_crops": req.primary_crops}


@app.post("/api/login")
def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"user_id": user["id"], "username": user["username"], "region": user["region"], "primary_crops": user["primary_crops"]}


# Chat (Barbale pipeline)
class NewSessionRequest(BaseModel):
    user_id: int


class ChatRequest(BaseModel):
    user_id: int
    session_id: int
    message_ka: str


@app.post("/api/sessions", status_code=201)
def new_session(req: NewSessionRequest):
    session_id = create_chat_session(req.user_id)
    return {"session_id": session_id}


@app.get("/api/sessions/{user_id}")
def list_sessions(user_id: int):
    return get_chat_sessions(user_id)


@app.get("/api/sessions/{session_id}/messages")
def list_messages(session_id: int):
    return get_session_messages(session_id)


@app.post("/api/chat")
def chat(req: ChatRequest):
    query_en = _translate(req.message_ka, "ka", "en")
    response_en = _ask_ollama(query_en)
    response_ka = _translate(response_en, "en", "ka")
    add_chat_message(req.session_id, req.message_ka, query_en, response_en, response_ka)
    return {"response_ka": response_ka, "response_en": response_en}


# Scan (Koi pipeline)
@app.post("/api/scan")
async def scan(user_id: int, file: UploadFile = File(...)):
    image_bytes = await file.read()
    result = classify(image_bytes)

    advice_en, advice_ka = None, None
    if result["freshness"] == "Rotten":
        advice_en = _ask_ollama(
            f"A rotten {result['produce']} was detected in the inventory. "
            "Provide a brief, actionable recommendation on how to isolate this produce "
            "and stop the rot or mold from spreading to neighboring items in storage."
        )
        advice_ka = _translate(advice_en, "en", "ka")

    create_alert_log(user_id, result["produce"], result["freshness"], result["confidence"], advice_en, advice_ka)
    return {**result, "advice_ka": advice_ka}


@app.get("/api/alerts/{user_id}")
def list_alerts(user_id: int):
    return get_alert_logs(user_id)
