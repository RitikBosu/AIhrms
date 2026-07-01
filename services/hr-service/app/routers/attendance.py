from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_session
from app.models import Attendance, Employee
from app.routers.deps import get_current_user

router = APIRouter()


def require_role(user, allowed_roles):
    if user["role"] not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission for this action.")


class AttendanceMark(BaseModel):
    employeeId: Optional[int] = None
    date: str
    status: str


class BulkRecord(BaseModel):
    employeeId: int
    date: str
    status: str


class BulkAttendance(BaseModel):
    records: List[BulkRecord]


def _get_emp_for_user(session: Session, user_id: int) -> Optional[Employee]:
    return session.exec(select(Employee).where(Employee.user_id == user_id)).first()


def _serialize(a: Attendance) -> dict:
    return {"id": a.id, "employeeId": a.employee_id, "date": a.date, "status": a.status}


@router.get("/attendance")
def get_attendance(session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    if user["role"] == "employee":
        emp = _get_emp_for_user(session, user["id"])
        if not emp:
            return []
        rows = session.exec(select(Attendance).where(Attendance.employee_id == emp.id)).all()
        return [_serialize(r) for r in rows]
    rows = session.exec(select(Attendance)).all()
    return [_serialize(r) for r in rows]


@router.post("/attendance", status_code=status.HTTP_201_CREATED)
def mark_attendance(att_in: AttendanceMark, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    today = datetime.now().strftime("%Y-%m-%d")
    if att_in.date > today:
        raise HTTPException(status_code=400, detail="Cannot mark attendance for a future date.")

    emp_id = att_in.employeeId
    if user["role"] == "employee":
        emp = _get_emp_for_user(session, user["id"])
        if not emp:
            raise HTTPException(status_code=404, detail="No employee record linked to your account.")
        emp_id = emp.id

    att = Attendance(employee_id=emp_id, date=att_in.date, status=att_in.status)
    session.add(att)
    session.commit()
    session.refresh(att)
    return _serialize(att)


@router.post("/attendance/bulk")
def bulk_attendance(bulk_in: BulkAttendance, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_role(user, ["admin", "hr"])
    inserted, skipped, errors = 0, 0, []

    for i, rec in enumerate(bulk_in.records):
        emp = session.get(Employee, rec.employeeId)
        if not emp:
            errors.append({"row": i+1, "reason": f"Employee {rec.employeeId} not found"})
            continue
        if rec.status not in ["Present", "Absent"]:
            errors.append({"row": i+1, "reason": f"Invalid status: {rec.status}"})
            continue
        existing = session.exec(
            select(Attendance)
            .where(Attendance.employee_id == rec.employeeId)
            .where(Attendance.date == rec.date)
        ).first()
        if existing:
            skipped += 1
            continue
        session.add(Attendance(employee_id=rec.employeeId, date=rec.date, status=rec.status))
        inserted += 1

    session.commit()
    return {"inserted": inserted, "skipped": skipped, "errors": errors}
