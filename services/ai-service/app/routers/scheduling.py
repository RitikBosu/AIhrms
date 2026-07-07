from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.services.ai_utils import generate_roster_prompt

router = APIRouter()

class AIScheduleRequest(BaseModel):
    prompt: str
    start_date: str
    end_date: str
    context: Dict[str, Any]

@router.post("/ai-schedule")
def ai_schedule(payload: AIScheduleRequest):
    try:
        draft = generate_roster_prompt(
            prompt=payload.prompt,
            start_date=payload.start_date,
            end_date=payload.end_date,
            context=payload.context
        )
        return draft
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
