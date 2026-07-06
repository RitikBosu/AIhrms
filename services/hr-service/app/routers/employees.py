from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from pydantic import BaseModel, EmailStr, field_validator, constr
from typing import Optional
import time, os

from app.database import get_session
from app.models import Employee, User, AuditLog
from app.routers.deps import get_current_user
import datetime

router = APIRouter()


def require_role(user, allowed_roles):
    if user["role"] not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission for this action.")


def create_id():
    return f"emp-{int(time.time()*1000)}-{os.urandom(3).hex()}"


class EmployeeCreate(BaseModel):
    name: str
    email: EmailStr
    department: str
    designation: str
    salary: float
    joiningDate: str

    @field_validator("name", "department", "designation", "joiningDate")
    @classmethod
    def not_empty(cls, v):
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v

    @field_validator("salary")
    @classmethod
    def check_salary(cls, v):
        if v <= 0:
            raise ValueError("Salary must be greater than 0")
        return v


class EmployeeUpdate(EmployeeCreate):
    pass


@router.get("/employees")
def get_employees(skip: int = 0, limit: int = 100, include_deleted: bool = False, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    if user["role"] == "employee":
        query = select(Employee).where(Employee.user_id == user["id"])
        if not include_deleted:
            query = query.where(Employee.is_deleted == False)
        emp = session.exec(query).first()
        return [_serialize(emp)] if emp else []
        
    query = select(Employee)
    if not include_deleted:
        query = query.where(Employee.is_deleted == False)
        
    emps = session.exec(query.offset(skip).limit(limit)).all()
    return [_serialize(e) for e in emps]


@router.post("/employees", status_code=status.HTTP_201_CREATED)
def create_employee(emp_in: EmployeeCreate, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_role(user, ["admin", "hr"])
    emp = Employee(
        name=emp_in.name,
        email=emp_in.email,
        department=emp_in.department,
        designation=emp_in.designation,
        salary=emp_in.salary,
        joining_date=emp_in.joiningDate,
    )
    session.add(emp)
    session.commit()
    session.refresh(emp)
    
    log = AuditLog(
        user_id=user["id"],
        action="CREATE_EMPLOYEE",
        target_id=str(emp.id),
        details=f"Created employee {emp.name}",
        timestamp=str(datetime.datetime.now())
    )
    session.add(log)
    session.commit()
    
    return _serialize(emp)


@router.put("/employees/{emp_id}")
def update_employee(emp_id: int, emp_in: EmployeeUpdate, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_role(user, ["admin", "hr"])
    emp = session.get(Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found.")
    emp.name = emp_in.name
    emp.email = emp_in.email
    emp.department = emp_in.department
    emp.designation = emp_in.designation
    emp.salary = emp_in.salary
    emp.joining_date = emp_in.joiningDate
    session.add(emp)
    session.commit()
    session.refresh(emp)

    log = AuditLog(
        user_id=user["id"],
        action="UPDATE_EMPLOYEE",
        target_id=str(emp.id),
        details=f"Updated employee {emp.name}",
        timestamp=str(datetime.datetime.now())
    )
    session.add(log)
    session.commit()

    return _serialize(emp)


@router.delete("/employees/{emp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(emp_id: int, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_role(user, ["admin"])
    emp = session.get(Employee, emp_id)
    if not emp or emp.is_deleted:
        raise HTTPException(status_code=404, detail="Employee not found.")
    emp.is_deleted = True
    session.add(emp)
    session.commit()

    log = AuditLog(
        user_id=user["id"],
        action="DELETE_EMPLOYEE",
        target_id=str(emp.id),
        details=f"Soft deleted employee {emp.name}",
        timestamp=str(datetime.datetime.now())
    )
    session.add(log)
    session.commit()


@router.post("/employees/{emp_id}/restore")
def restore_employee(emp_id: int, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_role(user, ["admin"])
    emp = session.get(Employee, emp_id)
    if not emp or not emp.is_deleted:
        raise HTTPException(status_code=404, detail="Employee not found or not deleted.")
        
    emp.is_deleted = False
    session.add(emp)
    session.commit()
    
    log = AuditLog(
        user_id=user["id"],
        action="RESTORE_EMPLOYEE",
        target_id=str(emp.id),
        details=f"Restored employee {emp.name}",
        timestamp=str(datetime.datetime.now())
    )
    session.add(log)
    session.commit()
    
    session.refresh(emp)
    return _serialize(emp)


def _serialize(emp: Employee) -> dict:
    return {
        "id": emp.id,
        "name": emp.name,
        "email": emp.email,
        "department": emp.department,
        "designation": emp.designation,
        "salary": emp.salary,
        "joiningDate": emp.joining_date,
        "userId": emp.user_id,
        "isDeleted": emp.is_deleted,
    }
