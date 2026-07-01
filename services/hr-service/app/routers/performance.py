from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional

from app.database import get_session
from app.models import PerformanceReview, Employee
from app.routers.deps import get_current_user
from app.services.ai_utils import call_groq, create_performance_summary_fallback

router = APIRouter()


def require_role(user, allowed_roles):
    if user["role"] not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission for this action.")


def _get_emp_for_user(session: Session, user_id: int) -> Optional[Employee]:
    return session.exec(select(Employee).where(Employee.user_id == user_id)).first()


def _serialize(r: PerformanceReview) -> dict:
    return {
        "id": r.id,
        "employeeId": r.employee_id,
        "rating": r.rating,
        "feedback": r.feedback,
        "aiSummary": r.ai_summary,
    }


class PerformanceCreate(BaseModel):
    employeeId: int
    rating: float
    feedback: str


@router.get("/performance")
def get_performance(session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    if user["role"] == "employee":
        emp = _get_emp_for_user(session, user["id"])
        if not emp:
            return []
        rows = session.exec(select(PerformanceReview).where(PerformanceReview.employee_id == emp.id)).all()
        return [_serialize(r) for r in rows]
    rows = session.exec(select(PerformanceReview)).all()
    return [_serialize(r) for r in rows]


@router.post("/performance", status_code=status.HTTP_201_CREATED)
def create_performance(perf_in: PerformanceCreate, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_role(user, ["admin", "manager"])
    emp = session.get(Employee, perf_in.employeeId)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found.")

    ai_summary = ""
    try:
        sys_p = "You are a professional HR performance review writer at FWC IT Services. Write concise, constructive reviews. Respond with ONLY the review text, no JSON or markdown."
        user_p = f"Write a professional performance review summary for {emp.name} who received a rating of {perf_in.rating}/5.\nManager's feedback: \"{perf_in.feedback}\"\nRequirements:\n- Exactly 3 sentences\n- Professional and constructive tone\n- End with one specific, actionable next-step goal"
        ai_summary = call_groq(sys_p, user_p)
    except Exception as e:
        print("Groq performance summary fallback:", e)
        ai_summary = create_performance_summary_fallback(emp.name, float(perf_in.rating), perf_in.feedback)

    review = PerformanceReview(
        employee_id=perf_in.employeeId,
        rating=float(perf_in.rating),
        feedback=perf_in.feedback,
        ai_summary=ai_summary,
    )
    session.add(review)
    session.commit()
    session.refresh(review)
    return _serialize(review)
