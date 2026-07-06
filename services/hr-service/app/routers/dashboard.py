from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func

from app.database import get_session
from app.models import Employee, Attendance, Leave, PerformanceReview
from app.routers.deps import get_current_user

router = APIRouter()


def _get_emp_for_user(session, user_id):
    return session.exec(select(Employee).where(Employee.user_id == user_id)).first()


@router.get("/dashboard")
def get_dashboard(session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")

    employee_count = session.exec(select(func.count(Employee.id))).one()
    pending_leaves = session.exec(select(func.count(Leave.id)).where(Leave.status == "Pending")).one()
    present_today = session.exec(
        select(func.count(Attendance.id))
        .where(Attendance.date == today)
        .where(Attendance.status == "Present")
    ).one()

    employee = _get_emp_for_user(session, user["id"]) if user["role"] == "employee" else None

    result = {
        "employeeCount": employee_count,
        "pendingLeaves": pending_leaves,
        "presentToday": present_today,
    }

    # Per-employee activity
    if employee:
        my_att = session.exec(select(Attendance).where(Attendance.employee_id == employee.id)).all()
        my_present = sum(1 for a in my_att if a.status == "Present")
        my_att_rate = round((my_present / len(my_att)) * 100) if my_att else 100
        my_leaves = session.exec(select(Leave).where(Leave.employee_id == employee.id)).all()
        result["myActivity"] = {
            "myAttendanceRate": my_att_rate,
            "myLeaveBalance": {
                "total": 18,
                "used": sum(1 for l in my_leaves if l.status == "Approved"),
                "pending": sum(1 for l in my_leaves if l.status == "Pending"),
            },
        }

    # Admin overview
    if user["role"] == "admin":
        all_att = session.exec(select(Attendance)).all()
        total = len(all_att)
        present = sum(1 for a in all_att if a.status == "Present")
        overall_rate = round((present / total) * 100) if total else 100

        all_perf = session.exec(select(PerformanceReview)).all()
        risk_levels = ["high" if p.rating < 3 else "medium" if p.rating < 4 else "low" for p in all_perf]
        
        # Avg Salary by Dept
        all_emps = session.exec(select(Employee).where(Employee.is_deleted == False)).all()
        dept_salary = {}
        for e in all_emps:
            dept_salary.setdefault(e.department, []).append(e.salary or 0)
        avg_salary_by_dept = [{"department": k, "avgSalary": round(sum(v)/len(v))} for k, v in dept_salary.items()]

        # Leave Approval Rate
        all_leaves = session.exec(select(Leave)).all()
        approved = sum(1 for l in all_leaves if l.status == "Approved")
        rejected = sum(1 for l in all_leaves if l.status == "Rejected")
        pending = sum(1 for l in all_leaves if l.status == "Pending")

        result["companyOverview"] = {
            "totalEmployees": employee_count,
            "overallAttendanceRate": overall_rate,
            "attritionRiskSummary": {
                "low": risk_levels.count("low"),
                "medium": risk_levels.count("medium"),
                "high": risk_levels.count("high"),
            },
            "avgSalaryByDepartment": avg_salary_by_dept,
            "leaveApprovalRate": {
                "approved": approved,
                "rejected": rejected,
                "pending": pending
            }
        }

    return result
