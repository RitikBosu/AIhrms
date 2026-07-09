from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
import time
import requests

from app.database import get_session
from app.models import Leave, Employee
from app.models.shifts import Shift
from app.routers.deps import get_current_user

router = APIRouter()


def require_role(user, allowed_roles):
    if user["role"] not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission for this action.")


class LeaveRequest(BaseModel):
    employeeId: Optional[int] = None
    fromDate: str
    toDate: str
    type: str
    reason: str

    @field_validator("fromDate", "toDate", "type", "reason")
    @classmethod
    def not_empty(cls, v):
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v

    @field_validator("type")
    @classmethod
    def check_type(cls, v):
        allowed = ["Sick", "Casual", "Earned", "Unpaid"]
        if v not in allowed:
            raise ValueError(f"Type must be one of {allowed}")
        return v


class LeaveAction(BaseModel):
    action: str  # approve | reject


def _get_emp_for_user(session: Session, user_id: int) -> Optional[Employee]:
    return session.exec(select(Employee).where(Employee.user_id == user_id)).first()


def _serialize(l: Leave) -> dict:
    return {
        "id": l.id,
        "employeeId": l.employee_id,
        "fromDate": l.from_date,
        "toDate": l.to_date,
        "type": l.type,
        "reason": l.reason,
        "status": l.status,
        "requestedOn": l.requested_on,
        "aiJustification": l.ai_justification,
    }


@router.get("/leaves")
def get_leaves(session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    if user["role"] == "employee":
        emp = _get_emp_for_user(session, user["id"])
        if not emp:
            return []
        rows = session.exec(select(Leave).where(Leave.employee_id == emp.id)).all()
        return [_serialize(r) for r in rows]
    rows = session.exec(select(Leave)).all()
    return [_serialize(r) for r in rows]


@router.post("/leaves", status_code=status.HTTP_201_CREATED)
def request_leave(leave_in: LeaveRequest, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    emp_id = leave_in.employeeId
    if user["role"] == "employee":
        emp = _get_emp_for_user(session, user["id"])
        if not emp:
            raise HTTPException(status_code=404, detail="No employee record linked to your account.")
    else:
        emp = session.get(Employee, emp_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found.")

    emp_id = emp.id

    # 1. Calculate requested days
    try:
        f_date = datetime.strptime(leave_in.fromDate, "%Y-%m-%d")
        t_date = datetime.strptime(leave_in.toDate, "%Y-%m-%d")
        days_requested = (t_date - f_date).days + 1
        if days_requested <= 0:
            raise ValueError("End date must be after start date")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Check Balances
    is_sick = leave_in.type == "Sick"
    balance_available = emp.sick_leave_balance_days if is_sick else emp.pto_balance_days
    
    # 3. Check Department Coverage
    # Get shifts for the employee's department on these dates
    # We find employees in the same department, and count shifts assigned to them during this period
    dept_employees = session.exec(select(Employee).where(Employee.department == emp.department)).all()
    dept_emp_ids = [e.id for e in dept_employees if e.id is not None]
    
    # Set to end of day for t_date
    t_date_end = t_date.replace(hour=23, minute=59, second=59)

    shifts_in_period = session.exec(
        select(Shift)
        .where(Shift.start_time >= f_date)
        .where(Shift.end_time <= t_date_end)
    ).all()
    
    # Count distinct active employees working during this period in this department
    working_emp_ids = {s.employee_id for s in shifts_in_period if s.employee_id in dept_emp_ids}
    coverage_count = len(working_emp_ids)

    # 4. Call AI Service for Evaluation
    ai_status = "Pending"
    ai_justification = None
    
    try:
        payload = {
            "leave_type": leave_in.type,
            "days_requested": days_requested,
            "balance_available": balance_available,
            "department": emp.department,
            "coverage_count": coverage_count,
            "total_department_size": len(dept_emp_ids),
            "reason": leave_in.reason
        }
        # Note: ai-service runs on 8002
        ai_resp = requests.post("http://127.0.0.1:8002/api/leave/evaluate", json=payload, timeout=10)
        
        if ai_resp.ok:
            data = ai_resp.json()
            ai_status = data.get("status", "Pending")
            ai_justification = data.get("justification", "No justification provided.")
        else:
            print("AI Service returned error:", ai_resp.text)
            ai_justification = "AI evaluation failed. Manual review required."
    except Exception as e:
        print("AI Service request failed:", e)
        ai_justification = "AI service unreachable. Manual review required."

    # 5. Apply Results
    final_status = ai_status
    if final_status == "Approved":
        # Deduct balance
        if leave_in.type != "Unpaid":
            if is_sick:
                emp.sick_leave_balance_days -= days_requested
            else:
                emp.pto_balance_days -= days_requested
            session.add(emp)

    leave = Leave(
        employee_id=emp_id,
        from_date=leave_in.fromDate,
        to_date=leave_in.toDate,
        type=leave_in.type,
        reason=leave_in.reason,
        status=final_status,
        requested_on=time.strftime("%Y-%m-%d"),
        ai_justification=ai_justification
    )
    session.add(leave)
    session.commit()
    session.refresh(leave)
    return _serialize(leave)


@router.post("/leaves/{leave_id}")
def process_leave(leave_id: int, action_in: LeaveAction, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_role(user, ["admin", "hr"])
    leave = session.get(Leave, leave_id)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found.")
        
    emp = session.get(Employee, leave.employee_id)
    
    # Calculate days
    f_date = datetime.strptime(leave.from_date, "%Y-%m-%d")
    t_date = datetime.strptime(leave.to_date, "%Y-%m-%d")
    days_requested = (t_date - f_date).days + 1
    is_sick = leave.type == "Sick"

    if action_in.action == "approve":
        if leave.status != "Approved": # Only deduct if it wasn't already approved
            if leave.type != "Unpaid" and emp:
                if is_sick:
                    emp.sick_leave_balance_days -= days_requested
                else:
                    emp.pto_balance_days -= days_requested
                session.add(emp)
        leave.status = "Approved"
    elif action_in.action == "reject":
        if leave.status == "Approved": # Refund if it was previously approved
            if leave.type != "Unpaid" and emp:
                if is_sick:
                    emp.sick_leave_balance_days += days_requested
                else:
                    emp.pto_balance_days += days_requested
                session.add(emp)
        leave.status = "Rejected"
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")
        
    session.add(leave)
    session.commit()
    session.refresh(leave)
    return _serialize(leave)

@router.get("/leaves/balances")
def get_balances(session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    if user["role"] == "employee":
        emp = _get_emp_for_user(session, user["id"])
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        return {
            "pto_balance_days": emp.pto_balance_days,
            "sick_leave_balance_days": emp.sick_leave_balance_days
        }
    return {}
