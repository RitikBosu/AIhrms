from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime
import time
import os

from app.routers.deps import get_current_user
from app.services.db import read_db, write_db

from app.services.utils import create_id, require_role, get_employee_for_user

router = APIRouter()

ROLE_ACCESS = {
    "hr": ["admin", "hr"]
}

class AttendanceMark(BaseModel):
    employeeId: Optional[str] = None
    date: str
    status: str

class AttendanceRecord(BaseModel):
    employeeId: str
    date: str
    status: str

class BulkAttendance(BaseModel):
    records: List[AttendanceRecord]

@router.get("/attendance")
def get_attendance(user: dict = Depends(get_current_user)):
    db = read_db()
    if user["role"] == "employee":
        emp = get_employee_for_user(db, user["id"])
        rows = [r for r in db.get("attendance", []) if r.get("employeeId") == emp["id"]] if emp else []
        return rows
    return db.get("attendance", [])

@router.post("/attendance", status_code=status.HTTP_201_CREATED)
def mark_attendance(att_in: AttendanceMark, user: dict = Depends(get_current_user)):
    db = read_db()
    today = datetime.now().strftime("%Y-%m-%d")
    if att_in.date > today:
        raise HTTPException(status_code=400, detail="Cannot mark attendance for a future date.")
        
    emp = get_employee_for_user(db, user["id"]) if user["role"] == "employee" else None
    att = {
        "id": create_id("att"),
        "employeeId": emp["id"] if emp else att_in.employeeId,
        "date": att_in.date,
        "status": att_in.status
    }
    db.setdefault("attendance", []).append(att)
    write_db(db)
    return att

@router.post("/attendance/bulk")
def bulk_attendance(bulk_in: BulkAttendance, user: dict = Depends(get_current_user)):
    require_role(user, ROLE_ACCESS["hr"])
    db = read_db()
    records = bulk_in.records
    
    inserted, skipped, errors = 0, 0, []
    for i, rec in enumerate(records):
        emp = next((e for e in db.get("employees", []) if e["id"] == rec.employeeId), None)
        if not emp:
            errors.append({"row": i+1, "reason": f"Employee {rec.employeeId} not found"})
            continue
        if rec.status not in ["Present", "Absent"]:
            errors.append({"row": i+1, "reason": f"Invalid status: {rec.status}. Must be Present or Absent"})
            continue
        
        duplicate = next((a for a in db.get("attendance", []) if a["employeeId"] == rec.employeeId and a["date"] == rec.date), None)
        if duplicate:
            skipped += 1
            continue
            
        db.setdefault("attendance", []).append({
            "id": create_id("att"),
            "employeeId": rec.employeeId,
            "date": rec.date,
            "status": rec.status
        })
        inserted += 1
        
    write_db(db)
    return {"inserted": inserted, "skipped": skipped, "errors": errors}
