"""
SQLite database for meetings, transcripts, summaries.
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import List, Dict

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./meeting_assistant.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    participants = Column(JSON)  # list of emails/names
    active = Column(Boolean, default=True)
    
    transcripts = relationship("Transcript", back_populates="meeting")
    summary = relationship("Summary", back_populates="meeting", uselist=False)

class Transcript(Base):
    __tablename__ = "transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    speaker = Column(String, nullable=True)
    text = Column(Text)
    
    meeting = relationship("Meeting", back_populates="transcripts")

class Summary(Base):
    __tablename__ = "summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), unique=True)
    short_summary = Column(Text)
    detailed_summary = Column(Text)
    action_items = Column(JSON)
    decisions = Column(JSON)
    topics = Column(JSON)
    
    meeting = relationship("Meeting", back_populates="summary")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helpers
def create_meeting(title: str, participants: List[str] = None) -> Meeting:
    db = next(get_db())
    meeting = Meeting(title=title, participants=participants or [])
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting

def add_transcript_chunk(meeting_id: int, text: str, speaker: str = None):
    db = next(get_db())
    transcript = Transcript(meeting_id=meeting_id, text=text, speaker=speaker)
    db.add(transcript)
    db.commit()

def save_summary(meeting_id: int, summary_data: Dict):
    db = next(get_db())
    summary = Summary(
        meeting_id=meeting_id,
        short_summary=summary_data["short_summary"],
        detailed_summary=summary_data["detailed_summary"],
        action_items=summary_data["action_items"],
        decisions=summary_data["decisions"],
        topics=summary_data["topics"]
    )
    db.add(summary)
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    meeting.end_time = datetime.utcnow()
    meeting.active = False
    db.commit()

def get_meeting_history(limit: int = 10) -> List[Dict]:
    db = next(get_db())
    meetings = db.query(Meeting).order_by(Meeting.start_time.desc()).limit(limit).all()
    return [{"id": m.id, "title": m.title, "start": m.start_time, "summary": m.summary.short_summary if m.summary else None} for m in meetings]

