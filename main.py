# backend/main.py
import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import databases
import sqlalchemy
import uuid
import aiofiles
from models import Message, SOS, Base
import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./wristbridge.db")
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
app = FastAPI(title="WristBridge Backend")

# Use SQLAlchemy engine for creating tables
engine = sqlalchemy.create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)

# Pydantic models
class SendMessage(BaseModel):
    sender_id: str
    recipient_id: Optional[str] = None
    msg_type: str
    text: Optional[str] = None

class SendSOS(BaseModel):
    user_id: str
    lat: float
    lon: float
    note: Optional[str] = None

# Helper: save uploaded file and return path
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def save_upload_file(upload_file: UploadFile) -> str:
    ext = os.path.splitext(upload_file.filename)[1] or ".bin"
    fname = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, fname)
    async with aiofiles.open(path, 'wb') as out_file:
        content = await upload_file.read()
        await out_file.write(content)
    return path

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Endpoints
@app.post("/send_message")
async def send_message(payload: SendMessage):
    query = "INSERT INTO messages (sender_id, recipient_id, msg_type, text, created_at) VALUES (:sender_id, :recipient_id, :msg_type, :text, :created_at)"
    values = {
        "sender_id": payload.sender_id,
        "recipient_id": payload.recipient_id,
        "msg_type": payload.msg_type,
        "text": payload.text,
        "created_at": datetime.datetime.utcnow()
    }
    await database.execute(query=query, values=values)
    return {"status": "ok"}

@app.post("/send_voice/")
async def send_voice(sender_id: str = Form(...), recipient_id: Optional[str] = Form(None), file: UploadFile = File(...)):
    # save file
    path = await save_upload_file(file)
    query = "INSERT INTO messages (sender_id, recipient_id, msg_type, media_url, created_at) VALUES (:sender_id, :recipient_id, :msg_type, :media_url, :created_at)"
    values = {"sender_id": sender_id, "recipient_id": recipient_id, "msg_type": "stt_audio", "media_url": path, "created_at": datetime.datetime.utcnow()}
    await database.execute(query=query, values=values)
    return {"status": "ok", "path": path}

@app.post("/send_sos")
async def send_sos(payload: SendSOS):
    query = "INSERT INTO sos (user_id, lat, lon, note, created_at) VALUES (:user_id, :lat, :lon, :note, :created_at)"
    values = {
        "user_id": payload.user_id,
        "lat": payload.lat,
        "lon": payload.lon,
        "note": payload.note,
        "created_at": datetime.datetime.utcnow()
    }
    await database.execute(query=query, values=values)
    return {"status": "ok"}

@app.get("/messages")
async def get_messages(since: Optional[str] = None):
    q = "SELECT id, sender_id, recipient_id, msg_type, text, media_url, created_at FROM messages ORDER BY created_at DESC LIMIT 200"
    rows = await database.fetch_all(q)
    result = [dict(r) for r in rows]
    return JSONResponse(result)

@app.get("/sos")
async def list_sos():
    q = "SELECT id, user_id, lat, lon, note, created_at FROM sos ORDER BY created_at DESC LIMIT 200"
    rows = await database.fetch_all(q)
    return JSONResponse([dict(r) for r in rows])

@app.get("/uploads/{fname}")
def download_upload(fname: str):
    path = os.path.join(UPLOAD_DIR, fname)
    if not os.path.exists(path):
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path)
