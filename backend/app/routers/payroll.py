from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from app.routers.deps import get_current_user
from app.services.db import read_db

from app.services.utils import get_employee_for_user

router = APIRouter()

def calculate_payroll_for_employee(emp, db):
    att = [a for a in db.get("attendance", []) if a.get("employeeId") == emp["id"]]
    present_days = len([a for a in att if a.get("status") == "Present"])
    absent_days = len([a for a in att if a.get("status") == "Absent"])
    
    salary = float(emp.get("salary", 0))
    allowance = round(salary * 0.1)
    deduction = absent_days * 500
    
    return {
        "employeeId": emp["id"],
        "name": emp["name"],
        "basicSalary": salary,
        "presentDays": present_days,
        "absentDays": absent_days,
        "allowance": allowance,
        "deduction": deduction,
        "netSalary": salary + allowance - deduction
    }

@router.get("/payroll")
def get_payroll(user: dict = Depends(get_current_user)):
    db = read_db()
    if user["role"] == "employee":
        emp = get_employee_for_user(db, user["id"])
        return [calculate_payroll_for_employee(emp, db)] if emp else []
    
    return [calculate_payroll_for_employee(e, db) for e in db.get("employees", [])]
