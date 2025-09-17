# backend/models.py
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime
)
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

def now_iso():
    return datetime.datetime.utcnow().isoformat()

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    sender_id = Column(String, nullable=False)
    recipient_id = Column(String, nullable=True)   # null => broadcast
    msg_type = Column(String, nullable=False)      # text | stt_audio | tts_audio | system
    text = Column(Text, nullable=True)
    media_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SOS(Base):
    __tablename__ = "sos"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
