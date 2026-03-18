"""
FastAPI backend for Smart Meeting Assistant.
Endpoints:
- POST /meetings/start: Create new meeting
- POST /transcribe: Audio chunk → append transcript (batch)
- POST /end_meeting/{meeting_id}: Generate & save summary
- GET /meetings: List recent meetings
- GET /meeting/{meeting_id}: Full details incl summary/transcript
Run: cd backend && uvicorn api:app --reload --port 8000
"""
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import base64

from dotenv import load_dotenv
load_dotenv()

from .core.db import init_db, create_meeting, add_transcript_chunk, save_summary, get_meeting_history, get_db, Meeting
from .core.speech import azure_stt_from_wav_bytes
from .core.llm import MeetingLLM

app = FastAPI(title="Smart Meeting Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Streamlit local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init
init_db()
llm = MeetingLLM()

class TranscribeRequest(BaseModel):
    meeting_id: int
    audio_base64: str
    language: str = "en-US"

class StartMeetingRequest(BaseModel):
    title: str = "Untitled Meeting"
    participants: Optional[List[str]] = None

@app.post("/meetings/start")
def start_meeting(req: StartMeetingRequest):
    meeting = create_meeting(req.title, req.participants)
    return {"meeting_id": meeting.id, "title": meeting.title, "start_time": meeting.start_time}

@app.post("/transcribe")
def transcribe(req: TranscribeRequest):
    try:
        audio_bytes = base64.b64decode(req.audio_base64)
        transcript = azure_stt_from_wav_bytes(audio_bytes, req.language)
        if transcript.strip():
            add_transcript_chunk(req.meeting_id, transcript)
        return {"transcript": transcript, "meeting_id": req.meeting_id}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/end_meeting/{meeting_id}")
def end_meeting(meeting_id: int):
    try:
        # Get full transcript
        db = next(get_db())
        transcripts = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).all()
        full_transcript = " ".join([t.text for t in transcripts])
        
        if not full_transcript.strip():
            raise HTTPException(400, "No transcript recorded")
        
        # Generate summary
        summary_data = llm.generate_summary(full_transcript, f"Meeting {meeting_id}")
        save_summary(meeting_id, summary_data)
        
        return {
            "meeting_id": meeting_id,
            "summary": summary_data,
            "full_transcript": full_transcript[:2000] + "..." if len(full_transcript) > 2000 else full_transcript
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/meetings")
def list_meetings(limit: int = 10):
    return get_meeting_history(limit)

@app.get("/meeting/{meeting_id}")
def get_meeting(meeting_id: int):
    db = next(get_db())
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    
    transcripts = [t.__dict__ for t in meeting.transcripts]
    summary = meeting.summary.__dict__ if meeting.summary else None
    
    return {
        "meeting": meeting.__dict__,
        "transcripts": transcripts,
        "summary": summary
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

