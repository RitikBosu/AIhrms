from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import List, Optional
import requests
import json
from datetime import datetime

from app.database import get_session
from app.models import Employee
from app.models.shifts import Shift, Availability
from app.models import Leave
from app.routers.deps import get_current_user

from app.services.roster_validator import (
    ProposedShift, EmployeeConstraints, AvailabilityWindow, LeaveRecord, ExistingShift,
    validate_roster, ValidationResult, Violation, ViolationType
)

router = APIRouter()

def require_role(user, allowed_roles):
    if user["role"] not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have permission for this action."
        )


class AIRosterRequest(BaseModel):
    prompt: str 
    start_date: str
    end_date: str


class ShiftResponsePayload(BaseModel):
    employee_id: int
    title: str
    start_time: datetime
    end_time: datetime


class ViolationPayload(BaseModel):
    shift_index: int
    type: str
    blocking: bool
    detail: str


class AIRosterResponse(BaseModel):
    approved_shifts: List[ShiftResponsePayload]
    violations: List[ViolationPayload]


@router.post("/generate-roster", response_model=AIRosterResponse)
def generate_roster(req: AIRosterRequest, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_role(user, ["admin", "hr", "manager"])
    
    # 1. Fetch eligible shift employees
    # Note: Using literal "SHIFT" since EmploymentType enum is applied
    emps = session.exec(select(Employee).where(Employee.employment_type == "SHIFT")).all()
    if not emps:
        raise HTTPException(status_code=400, detail="No shift-based employees found in database.")
        
    emp_dict = {e.id: EmployeeConstraints(id=e.id, max_weekly_hours=e.max_weekly_hours) for e in emps}
    
    # 2. Fetch Context Data (RAG pattern)
    availabilities = session.exec(select(Availability)).all()
    avail_windows = [
        AvailabilityWindow(
            employee_id=a.employee_id, 
            day_of_week=a.day_of_week, 
            start_time=a.start_time, 
            end_time=a.end_time,
            is_available=a.is_available
        )
        for a in availabilities
    ]
    
    # Fetch leaves overlapping the requested date range
    leaves = session.exec(
        select(Leave)
        .where(Leave.status == "Approved")
        .where(Leave.from_date <= req.end_date)
        .where(Leave.to_date >= req.start_date)
    ).all()
    
    leave_records = []
    for lv in leaves:
        if lv.employee_id:
            try:
                # Convert date strings to datetime for comparison
                s_date = datetime.strptime(lv.from_date, "%Y-%m-%d")
                e_date = datetime.strptime(lv.to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                leave_records.append(LeaveRecord(employee_id=lv.employee_id, start_date=s_date, end_date=e_date))
            except ValueError:
                pass
                
    # Fetch existing shifts to check for overlaps
    existing_db_shifts = session.exec(
        select(Shift)
        .where(Shift.start_time >= req.start_date)
        .where(Shift.end_time <= f"{req.end_date}T23:59:59")
    ).all()
    
    existing = [
        ExistingShift(employee_id=s.employee_id, start_time=s.start_time, end_time=s.end_time)
        for s in existing_db_shifts
    ]
    
    # 3. Call AI Service
    # We send the request to our local ai-service, passing anonymized IDs.
    ai_payload = {
        "prompt": req.prompt,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "context": {
            "employees": [{"id": e.id, "name": f"EMP_{e.id}"} for e in emps], # PII Masking
        }
    }
    
    try:
        # ai-service is running on port 8002 according to start.ps1
        ai_resp = requests.post("http://127.0.0.1:8002/api/ai-schedule", json=ai_payload)
        ai_resp.raise_for_status()
        ai_data = ai_resp.json() # List of {"employee_id": 1, "start_time": "...", "end_time": "..."}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI Service error: {str(e)}")
        
    # 4. Parse AI Output to ProposedShifts
    proposed_shifts = []
    for s in ai_data:
        try:
            st = datetime.fromisoformat(s["start_time"].replace("Z", "+00:00"))
            et = datetime.fromisoformat(s["end_time"].replace("Z", "+00:00"))
            # The AI might give "Morning Shift", else default
            title = s.get("title", "AI Generated Shift")
            proposed_shifts.append(ProposedShift(employee_id=s["employee_id"], start_time=st, end_time=et, title=title))
        except (ValueError, KeyError):
            continue
            
    # 5. Run Deterministic Validation
    val_result = validate_roster(proposed_shifts, emp_dict, avail_windows, leave_records, existing)
    
    # 6. Format response
    out_shifts = [
        ShiftResponsePayload(employee_id=ps.employee_id, title=ps.title, start_time=ps.start_time, end_time=ps.end_time)
        for ps in val_result.approved_shifts
    ]
    
    out_violations = [
        ViolationPayload(shift_index=v.shift_index, type=v.type.value, blocking=v.blocking, detail=v.detail)
        for v in val_result.violations
    ]
    
    return AIRosterResponse(approved_shifts=out_shifts, violations=out_violations)
