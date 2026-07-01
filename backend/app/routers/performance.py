from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import time
import os

from app.routers.deps import get_current_user
from app.services.db import read_db, write_db
from app.services.ai_utils import call_groq, create_performance_summary_fallback

router = APIRouter()

ROLE_ACCESS = {
    "manager": ["admin", "manager"]
}

def require_role(user, allowed_roles):
    if user["role"] not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission for this action.")

def create_id(prefix):
    return f"{prefix}-{int(time.time()*1000)}-{os.urandom(3).hex()}"

def get_employee_for_user(db, user_id):
    for emp in db.get("employees", []):
        if emp.get("userId") == user_id:
            return emp
    return None

class PerformanceReviewCreate(BaseModel):
    employeeId: str
    rating: float
    feedback: str

@router.get("/performance")
def get_performance(user: dict = Depends(get_current_user)):
    db = read_db()
    if user["role"] == "employee":
        emp = get_employee_for_user(db, user["id"])
        rows = [r for r in db.get("performance", []) if r.get("employeeId") == emp["id"]] if emp else []
        return rows
    return db.get("performance", [])

@router.post("/performance", status_code=status.HTTP_201_CREATED)
def create_performance(perf_in: PerformanceReviewCreate, user: dict = Depends(get_current_user)):
    require_role(user, ROLE_ACCESS["manager"])
    db = read_db()
    emp = next((e for e in db.get("employees", []) if e["id"] == perf_in.employeeId), None)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found.")
        
    ai_summary = ""
    try:
        sys_p = "You are a professional HR performance review writer at FWC IT Services. Write concise, constructive reviews. Respond with ONLY the review text, no JSON or markdown."
        user_p = f"Write a professional performance review summary for {emp['name']} who received a rating of {perf_in.rating}/5.\nManager's feedback: \"{perf_in.feedback}\"\nRequirements:\n- Exactly 3 sentences\n- Professional and constructive tone\n- Acknowledge strengths based on the rating\n- End with one specific, actionable next-step goal\n- Do NOT use bullet points or formatting, just plain sentences"
        ai_summary = call_groq(sys_p, user_p)
    except Exception as e:
        print("Groq performance summary fallback:", e)
        ai_summary = create_performance_summary_fallback(emp['name'], float(perf_in.rating), perf_in.feedback)

    review = {
        "id": create_id("perf"),
        "employeeId": perf_in.employeeId,
        "rating": float(perf_in.rating),
        "feedback": perf_in.feedback,
        "aiSummary": ai_summary
    }
    db.setdefault("performance", []).append(review)
    write_db(db)
    return review
