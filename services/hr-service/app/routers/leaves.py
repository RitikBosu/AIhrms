from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
import time

from app.database import get_session
from app.models import Leave, Employee
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
        emp_id = emp.id

    leave = Leave(
        employee_id=emp_id,
        from_date=leave_in.fromDate,
        to_date=leave_in.toDate,
        type=leave_in.type,
        reason=leave_in.reason,
        status="Pending",
        requested_on=time.strftime("%Y-%m-%d"),
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
    if action_in.action == "approve":
        leave.status = "Approved"
    elif action_in.action == "reject":
        leave.status = "Rejected"
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")
    session.add(leave)
    session.commit()
    session.refresh(leave)
    return _serialize(leave)
