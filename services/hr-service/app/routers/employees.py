from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
import time, os

from app.database import get_session
from app.models import Employee, User
from app.routers.deps import get_current_user

router = APIRouter()


def require_role(user, allowed_roles):
    if user["role"] not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission for this action.")


def create_id():
    return f"emp-{int(time.time()*1000)}-{os.urandom(3).hex()}"


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
def get_employees(session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    if user["role"] == "employee":
        emp = session.exec(select(Employee).where(Employee.user_id == user["id"])).first()
        return [_serialize(emp)] if emp else []
    emps = session.exec(select(Employee)).all()
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
    return _serialize(emp)


@router.delete("/employees/{emp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(emp_id: int, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_role(user, ["admin"])
    emp = session.get(Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found.")
    session.delete(emp)
    session.commit()


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
    }
