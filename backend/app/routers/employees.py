from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
import time
import os

from app.routers.deps import get_current_user
from app.services.db import read_db, write_db

from app.services.utils import create_id, require_role, get_employee_for_user

router = APIRouter()

ROLE_ACCESS = {
    "admin": ["admin", "hr", "manager", "employee"],
    "hr": ["admin", "hr"],
    "manager": ["admin", "manager"],
    "employee": ["admin", "hr", "manager", "employee"]
}

class EmployeeCreate(BaseModel):
    name: str
    email: str
    department: str
    designation: str
    salary: float
    joiningDate: str

class EmployeeUpdate(EmployeeCreate):
    pass

@router.get("/employees")
def get_employees(user: dict = Depends(get_current_user)):
    db = read_db()
    if user["role"] == "employee":
        emp = get_employee_for_user(db, user["id"])
        return [emp] if emp else []
    return db.get("employees", [])

@router.post("/employees", status_code=status.HTTP_201_CREATED)
def create_employee(emp_in: EmployeeCreate, user: dict = Depends(get_current_user)):
    require_role(user, ROLE_ACCESS["hr"])
    db = read_db()
    
    emp = {
        "id": create_id("emp"),
        "userId": "",
        "name": emp_in.name,
        "email": emp_in.email,
        "department": emp_in.department,
        "designation": emp_in.designation,
        "salary": emp_in.salary,
        "joiningDate": emp_in.joiningDate
    }
    
    db.setdefault("employees", []).append(emp)
    write_db(db)
    return emp

@router.put("/employees/{emp_id}")
def update_employee(emp_id: str, emp_in: EmployeeUpdate, user: dict = Depends(get_current_user)):
    require_role(user, ROLE_ACCESS["hr"])
    db = read_db()
    
    employees = db.get("employees", [])
    emp = next((e for e in employees if e["id"] == emp_id), None)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found.")
        
    emp.update({
        "name": emp_in.name,
        "email": emp_in.email,
        "department": emp_in.department,
        "designation": emp_in.designation,
        "salary": emp_in.salary,
        "joiningDate": emp_in.joiningDate
    })
    write_db(db)
    return emp

@router.delete("/employees/{emp_id}")
def delete_employee(emp_id: str, user: dict = Depends(get_current_user)):
    require_role(user, ["admin"])
    db = read_db()
    
    db["employees"] = [e for e in db.get("employees", []) if e["id"] != emp_id]
    write_db(db)
    return {"ok": True}
