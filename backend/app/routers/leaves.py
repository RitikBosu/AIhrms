from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import time
import os

from app.routers.deps import get_current_user
from app.services.db import read_db, write_db

from app.services.utils import create_id, require_role, get_employee_for_user

router = APIRouter()

ROLE_ACCESS = {
    "hr": ["admin", "hr"]
}

class LeaveRequest(BaseModel):
    employeeId: Optional[str] = None
    fromDate: str
    toDate: str
    type: str
    reason: str

class LeaveAction(BaseModel):
    action: str

@router.get("/leaves")
def get_leaves(user: dict = Depends(get_current_user)):
    db = read_db()
    if user["role"] == "employee":
        emp = get_employee_for_user(db, user["id"])
        rows = [r for r in db.get("leaves", []) if r.get("employeeId") == emp["id"]] if emp else []
        return rows
    return db.get("leaves", [])

@router.post("/leaves", status_code=status.HTTP_201_CREATED)
def request_leave(leave_in: LeaveRequest, user: dict = Depends(get_current_user)):
    db = read_db()
    emp = get_employee_for_user(db, user["id"]) if user["role"] == "employee" else None
    
    leave = {
        "id": create_id("leave"),
        "employeeId": emp["id"] if emp else leave_in.employeeId,
        "fromDate": leave_in.fromDate,
        "toDate": leave_in.toDate,
        "type": leave_in.type,
        "reason": leave_in.reason,
        "status": "Pending",
        "requestedOn": time.strftime("%Y-%m-%d")
    }
    
    db.setdefault("leaves", []).append(leave)
    write_db(db)
    return leave

@router.post("/leaves/{leave_id}")
def process_leave(leave_id: str, action_in: LeaveAction, user: dict = Depends(get_current_user)):
    require_role(user, ROLE_ACCESS["hr"])
    db = read_db()
    
    leaves = db.get("leaves", [])
    leave = next((l for l in leaves if l["id"] == leave_id), None)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found.")
        
    if action_in.action == "approve":
        leave["status"] = "Approved"
    elif action_in.action == "reject":
        leave["status"] = "Rejected"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    write_db(db)
    return leave
