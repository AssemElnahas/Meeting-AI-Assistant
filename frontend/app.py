"""
Streamlit frontend for Smart Meeting Assistant.
- Start meeting → live transcription via mic (streamlit-webrtc)
- Live transcript display
- End meeting → show summary/actions
- History search/export
"""
import streamlit as st
import requests
import base64
import io
import json
from datetime import datetime
from typing import List
import webrtcvad
import pyaudio  # for audio processing if needed
import streamlit_webrtc as webrtc

# Config
BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Smart Meeting Assistant", layout="wide")

# State
if "meeting_id" not in st.session_state:
    st.session_state.meeting_id = None
if "transcript_history" not in st.session_state:
    st.session_state.transcript_history = []
if "backend_ready" not in st.session_state:
    st.session_state.backend_ready = False

st.title("🤖 AI Smart Meeting Assistant")

tab1, tab2 = st.tabs(["Live Meeting", "History"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Controls")
        
        if st.button("📝 Start New Meeting"):
            title = st.text_input("Meeting Title", "Untitled Meeting").strip()
            if title:
                resp = requests.post(f"{BACKEND_URL}/meetings/start", json={"title": title})
                if resp.status_code == 200:
                    st.session_state.meeting_id = resp.json()["meeting_id"]
                    st.session_state.transcript_history = []
                    st.success(f"Meeting started! ID: {st.session_state.meeting_id}")
                else:
                    st.error("Failed to start meeting")
        
        if st.session_state.meeting_id:
            if st.button("🔚 End Meeting & Generate Summary", type="primary"):
                resp = requests.post(f"{BACKEND_URL}/end_meeting/{st.session_state.meeting_id}")
                if resp.status_code == 200:
                    summary_data = resp.json()
                    st.session_state.summary = summary_data
                    st.rerun()
                else:
                    st.error("Summary generation failed")
            
            st.info(f"**Active Meeting ID:** {st.session_state.meeting_id}")
    
    with col2:
        st.subheader("Live Transcript")
        if st.session_state.transcript_history:
            for entry in st.session_state.transcript_history[-10:]:  # Last 10
                st.markdown(f"**{entry.get('time', '')}:** {entry['text']}")
        else:
            st.info("Start recording to see live transcript...")
        
        # Audio recorder
        st.subheader("🎤 Microphone (Record chunks)")
        audio_recorder = webrtc.AudioRecorder(
            stream_size=1024,
            sample_rate=16000,
            num_channels=1
        )
        
        if audio_recorder.audio_bytes:
            # Send to backend
            if st.session_state.meeting_id:
                try:
                    audio_b64 = base64.b64encode(audio_recorder.audio_bytes).decode()
                    resp = requests.post(f"{BACKEND_URL}/transcribe", json={
                        "meeting_id": st.session_state.meeting_id,
                        "audio_base64": audio_b64,
                        "language": "en-US"
                    })
                    if resp.status_code == 200:
                        data = resp.json()
                        if data["transcript"].strip():
                            st.session_state.transcript_history.append({
                                "text": data["transcript"],
                                "time": datetime.now().strftime("%H:%M:%S")
                            })
                            st.rerun()
                except Exception as e:
                    st.error(f"Transcription error: {e}")

    # Summary display
    if "summary" in st.session_state:
        st.subheader("📄 AI Summary")
        summary = st.session_state.summary
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Short Summary**")
            st.write(summary.get("summary", {}).get("short_summary", ""))
        with col_b:
            st.markdown("**Key Topics**")
            for topic in summary.get("summary", {}).get("topics", []):
                st.markdown(f"- {topic}")
        
        st.markdown("**Action Items**")
        for action in summary.get("summary", {}).get("action_items", []):
            st.markdown(f"- {action}")
        
        # Download
        summary_text = f"Summary:\\n{json.dumps(summary.get('summary', {}), indent=2)}\\n\\nTranscript:\\n{summary.get('full_transcript', '')}"
        st.download_button("📥 Download Summary", summary_text, "meeting_summary.txt")

with tab2:
    st.subheader("Past Meetings")
    resp = requests.get(f"{BACKEND_URL}/meetings")
    if resp.status_code == 200:
        meetings = resp.json()
        for m in meetings:
            if st.button(f"{m['title']} ({m['start']})"):
                detail_resp = requests.get(f"{BACKEND_URL}/meeting/{m['id']}")
                if detail_resp.status_code == 200:
                    details = detail_resp.json()
                    st.json(details)

# Test backend connection
if st.sidebar.button("🧪 Test Backend"):
    try:
        resp = requests.get(f"{BACKEND_URL}/meetings")
        if resp.status_code == 200:
            st.sidebar.success("✅ Backend ready!")
            st.session_state.backend_ready = True
        else:
            st.sidebar.error("❌ Backend not running on port 8000")
    except:
        st.sidebar.error("❌ Cannot connect to backend")

st.sidebar.markdown("---")
st.sidebar.info("1. Run backend: `cd backend && pip install -r requirements.txt && uvicorn api:app --reload`\n2. Set .env keys\n3. Use mic to test!")

