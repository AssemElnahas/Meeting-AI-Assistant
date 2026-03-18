# AI Smart Meeting Assistant

Enterprise-grade real-time meeting transcription, summarization, and action item extraction.

## Features
- Real-time speech-to-text (Azure Speech SDK)
- Live captions/transcript
- LLM-powered summary & action items (OpenAI/gpt-4o-mini)
- Meeting history & search
- PDF export

## Quick Start

1. Clone/copy project to `smart_meeting_assistant/`
2. Backend:
   ```
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\\Scripts\\activate
   pip install -r requirements.txt
   cp ../.env.example .env  # Fill keys!
   uvicorn api:app --reload --port 8000
   ```
3. Frontend:
   ```
   cd frontend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   streamlit run app.py
   ```

## Architecture
- Backend: FastAPI + Azure Speech + OpenAI + SQLite
- Frontend: Streamlit + streamlit-webrtc (mic)

## API Endpoints
- POST /transcribe: Audio → transcript chunk
- POST /end_meeting: Generate summary/actions
- GET /meetings: History

## Scaling
- Docker: `docker-compose up`
- Azure: Deploy FastAPI to Azure App Service, use Azure Speech resource.

Test with mic in browser!

