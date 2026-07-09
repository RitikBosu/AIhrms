from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.ai_utils import call_groq, extract_json

router = APIRouter()

class LeaveEvaluateRequest(BaseModel):
    leave_type: str
    days_requested: int
    balance_available: float
    department: str
    coverage_count: int
    total_department_size: int
    reason: str


@router.post("/leave/evaluate")
def evaluate_leave(req: LeaveEvaluateRequest):
    # Rule 1: Insufficient Balance -> Pending immediately
    if req.leave_type != "Unpaid" and req.balance_available < req.days_requested:
        return {
            "status": "Pending",
            "justification": f"Insufficient {req.leave_type} balance. Requested: {req.days_requested}, Available: {req.balance_available}. Manager review required."
        }
        
    prompt = f"""
    You are an AI workforce manager for FWC HRMS.
    Evaluate the following leave request.
    
    Leave Details:
    - Type: {req.leave_type}
    - Days Requested: {req.days_requested}
    - Reason: {req.reason}
    
    Department Context:
    - Department: {req.department}
    - Total Employees in Dept: {req.total_department_size}
    - Employees Scheduled on these dates (Coverage): {req.coverage_count}
    
    Rules:
    1. If the coverage is critically low (less than 50% of department size), return "Pending" with a warning about low coverage.
    2. If coverage is adequate and they have enough balance, return "Approved".
    
    Return your response in STRICT JSON format:
    {{
        "status": "Approved" | "Pending",
        "justification": "A 1-2 sentence explanation."
    }}
    """
    
    sys_prompt = "You are an expert HR AI assistant evaluating leave requests. You output ONLY JSON."
    
    try:
        response_text = call_groq(sys_prompt, prompt)
        data = extract_json(response_text)
        return {
            "status": data.get("status", "Pending"),
            "justification": data.get("justification", "Fallback justification")
        }
    except Exception as e:
        return {
            "status": "Pending",
            "justification": f"AI Error: {str(e)}"
        }
