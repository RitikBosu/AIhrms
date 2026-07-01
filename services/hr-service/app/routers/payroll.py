from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models import Employee, Attendance
from app.routers.deps import get_current_user

router = APIRouter()


def _get_emp_for_user(session: Session, user_id: int):
    return session.exec(select(Employee).where(Employee.user_id == user_id)).first()


def _calc_payroll(emp: Employee, session: Session) -> dict:
    att = session.exec(select(Attendance).where(Attendance.employee_id == emp.id)).all()
    present_days = sum(1 for a in att if a.status == "Present")
    absent_days = sum(1 for a in att if a.status == "Absent")
    salary = float(emp.salary or 0)
    allowance = round(salary * 0.1)
    deduction = absent_days * 500
    return {
        "employeeId": emp.id,
        "name": emp.name,
        "basicSalary": salary,
        "presentDays": present_days,
        "absentDays": absent_days,
        "allowance": allowance,
        "deduction": deduction,
        "netSalary": salary + allowance - deduction,
    }


@router.get("/payroll")
def get_payroll(session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    if user["role"] == "employee":
        emp = _get_emp_for_user(session, user["id"])
        return [_calc_payroll(emp, session)] if emp else []
    emps = session.exec(select(Employee)).all()
    return [_calc_payroll(e, session) for e in emps]
