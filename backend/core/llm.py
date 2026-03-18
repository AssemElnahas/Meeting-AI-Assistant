"""
Meeting-specific LLM service using OpenAI/Azure OpenAI.
Custom prompts for summary, action items, decisions, topics.
"""
import os
from openai import OpenAI
from typing import List, Dict, Any
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Azure config
api_type = os.getenv("OPENAI_API_TYPE")
api_base = os.getenv("OPENAI_API_BASE")
api_version = os.getenv("OPENAI_API_VERSION", "2024-08-01-preview")
deployment = os.getenv("OPENAI_DEPLOYMENT_NAME")

class MeetingLLM:
    def __init__(self):
        pass  # client auto-configures from env
    
    def generate_summary(self, transcript: str, meeting_title: str = "Meeting") -> Dict[str, str]:
        \"\"\"
        Generate short/detailed summary + actions.
        \"\"\"
        prompt = f\"\"\"Meeting: {meeting_title}

Transcript:
{transcript}

Provide JSON:
{{
  "short_summary": "2-3 sentences key points",
  "detailed_summary": "Paragraph summary",
  "action_items": ["[Person] to [action] by [date]", ...],
  "decisions": ["Decision 1", ...],
  "topics": ["topic1", "topic2"]
}}\"\"\"

        response = client.chat.completions.create(
            model="gpt-4o-mini" if not deployment else deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return result
        except:
            # Fallback
            return {
                "short_summary": "Summary generation failed.",
                "detailed_summary": transcript[:500] + "...",
                "action_items": [],
                "decisions": [],
                "topics": []
            }
    
    def extract_speakers(self, transcript: str) -> List[Dict[str, str]]:
        \"\"\"
        Basic speaker diarization (future: integrate pyannote).
        \"\"\"
        prompt = f"Extract speakers from transcript (guess names):\\n{transcript[:2000]}\\nFormat: [{{\"speaker\": \"Name\", \"text\": \"quote\"}}]"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        
        return json.loads(response.choices[0].message.content or "[]")

