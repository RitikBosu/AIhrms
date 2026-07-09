from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import json

from app.services.ai_utils import call_groq, extract_json

router = APIRouter()

class EmployeeProfile(BaseModel):
    id: int
    name: str
    department: str
    max_weekly_hours: int
    performance_rating: float
    current_scheduled_hours: float  # We could calculate this from DB, but passing it is easier for MVP

class BiddingRequest(BaseModel):
    shift_title: str
    shift_start: str
    shift_end: str
    bidders: List[EmployeeProfile]


@router.post("/bidding/recommend")
def recommend_bidder(req: BiddingRequest):
    if not req.bidders:
        return {"recommended_employee_id": None, "justification": "No bidders."}
        
    prompt = f"""
    You are an AI workforce manager for FWC. You need to select the best employee to work an open shift.
    
    Open Shift Details:
    - Title: {req.shift_title}
    - Time: {req.shift_start} to {req.shift_end}
    
    Bidders:
    """
    for b in req.bidders:
        prompt += f"""
        Employee ID: {b.id}
        Name: {b.name}
        Department: {b.department}
        Max Weekly Hours (before Overtime): {b.max_weekly_hours}
        Currently Scheduled Hours this week: {b.current_scheduled_hours}
        Performance Rating (out of 5.0): {b.performance_rating}
        """
        
    prompt += """
    Criteria:
    1. Avoid Overtime: If an employee's (current_scheduled_hours + shift hours) exceeds max_weekly_hours, heavily penalize them as overtime is expensive.
    2. Performance: Prefer employees with higher performance ratings.
    
    Respond in STRICT JSON format with two keys:
    - "recommended_employee_id": The integer ID of the best employee to choose.
    - "justification": A 1-2 sentence explanation of why they were chosen (e.g. "Employee X is the best choice because they have a 4.9 rating and will not incur overtime pay.")
    """
    
    try:
        sys_prompt = "You are an AI workforce manager that selects the best employee for an open shift based on overtime cost and performance. Return STRICT JSON with 'recommended_employee_id' and 'justification'."
        response_text = call_groq(sys_prompt, prompt)
        data = extract_json(response_text)
        return data
    except Exception as e:
        return {"recommended_employee_id": req.bidders[0].id, "justification": f"Fallback to first bidder due to AI error: {str(e)}"}
