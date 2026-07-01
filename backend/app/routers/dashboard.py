from fastapi import APIRouter, Depends
from app.routers.deps import get_current_user
from app.services.db import read_db

router = APIRouter()

def get_employee_for_user(db, user_id):
    for emp in db.get("employees", []):
        if emp.get("userId") == user_id:
            return emp
    return None

@router.get("/dashboard")
def get_dashboard(user: dict = Depends(get_current_user)):
    db = read_db()
    employee = get_employee_for_user(db, user["id"])
    
    attendance_rows = db.get("attendance", [])
    if user["role"] == "employee" and employee:
        attendance_rows = [r for r in attendance_rows if r.get("employeeId") == employee["id"]]
        
    leave_rows = db.get("leaves", [])
    if user["role"] == "employee" and employee:
        leave_rows = [r for r in leave_rows if r.get("employeeId") == employee["id"]]

    employee_count = 1 if user["role"] == "employee" else len(db.get("employees", []))
    candidate_count = len(db.get("candidates", []))
    pending_leaves = len([l for l in leave_rows if l.get("status") == "Pending"])
    present_today = len([r for r in attendance_rows if r.get("status") == "Present"])

    result = {
        "employeeCount": employee_count,
        "candidateCount": candidate_count,
        "pendingLeaves": pending_leaves,
        "presentToday": present_today,
        "attendanceRows": attendance_rows,
        "leaveRows": leave_rows,
        "announcements": db.get("announcements", [])
    }

    my_attendance = [r for r in db.get("attendance", []) if r.get("employeeId") == employee["id"]] if employee else []
    my_leaves = [r for r in db.get("leaves", []) if r.get("employeeId") == employee["id"]] if employee else []
    my_present = len([a for a in my_attendance if a.get("status") == "Present"])
    my_attendance_rate = round((my_present / len(my_attendance)) * 100) if len(my_attendance) > 0 else 100

    result["myActivity"] = {
        "myAttendanceRate": my_attendance_rate,
        "myLeaveBalance": {
            "total": 18,
            "used": len([l for l in my_leaves if l.get("status") == "Approved"]),
            "pending": len([l for l in my_leaves if l.get("status") == "Pending"])
        },
        "recentActions": []
    }

    if user["role"] == "admin":
        risk_levels = ["high" if p.get("rating", 5) < 3 else "medium" if p.get("rating", 5) < 4 else "low" for p in db.get("performance", [])]
        overall_attendance_rate = 100
        total_attendance = len(db.get("attendance", []))
        if total_attendance > 0:
            overall_attendance_rate = round((len([a for a in db.get("attendance", []) if a.get("status") == "Present"]) / total_attendance) * 100)
            
        result["companyOverview"] = {
            "totalEmployees": len(db.get("employees", [])),
            "overallAttendanceRate": overall_attendance_rate,
            "totalOpenPositions": 3,
            "recentHires": 2,
            "attritionRiskSummary": {
                "low": len([r for r in risk_levels if r == "low"]),
                "medium": len([r for r in risk_levels if r == "medium"]),
                "high": len([r for r in risk_levels if r == "high"])
            }
        }

    if user["role"] == "hr":
        result["screeningStats"] = {
            "shortlisted": len([c for c in db.get("candidates", []) if c.get("aiDecision") == "Shortlisted"]),
            "underReview": len([c for c in db.get("candidates", []) if c.get("aiDecision") == "Under Review"]),
            "rejected": len([c for c in db.get("candidates", []) if c.get("aiDecision") == "Rejected"]),
        }

    return result
