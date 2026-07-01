"""
Seed script — migrates existing db.json data into Neon PostgreSQL.
Run once from: services/hr-service/
  python -m app.seed
"""
import os
import json
import sys
import hashlib

# Load .env from workspace root
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models import User, Employee, Attendance, Leave, PerformanceReview

# Path to legacy db.json
DB_JSON = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "backend", "data", "db.json"
)


def load_json():
    if not os.path.exists(DB_JSON):
        print(f"[ERROR] db.json not found at {DB_JSON}")
        sys.exit(1)
    with open(DB_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def seed():
    print("[seed] Creating tables...")
    create_db_and_tables()

    data = load_json()
    print(f"[seed] Loaded db.json - Users: {len(data.get('users', []))}, Employees: {len(data.get('employees', []))}")

    with Session(engine) as session:
        # ── Users ──────────────────────────────────────────────────────────
        user_id_map = {}  # old string id → new int id
        for u in data.get("users", []):
            existing = session.exec(select(User).where(User.email == u.get("email", ""))).first()
            if existing:
                user_id_map[u["id"]] = existing.id
                continue
            user = User(
                legacy_id=u.get("id"),
                username=u.get("name", u.get("email", "unknown")),
                email=u.get("email", ""),
                password_hash=u.get("passwordHash", ""),
                role=u.get("role", "employee"),
            )
            session.add(user)
            session.flush()
            user_id_map[u["id"]] = user.id
            print(f"  [OK] User: {user.email} ({user.role})")

        session.commit()

        # ── Employees ──────────────────────────────────────────────────────
        emp_id_map = {}  # old string id → new int id
        for e in data.get("employees", []):
            existing = session.exec(select(Employee).where(Employee.legacy_id == e.get("id"))).first()
            if existing:
                emp_id_map[e["id"]] = existing.id
                continue
            emp = Employee(
                legacy_id=e.get("id"),
                user_id=user_id_map.get(e.get("userId")),
                user_legacy_id=e.get("userId"),
                name=e.get("name", ""),
                email=e.get("email", ""),
                department=e.get("department", ""),
                designation=e.get("designation", ""),
                salary=float(e.get("salary", 0)),
                joining_date=e.get("joiningDate", ""),
            )
            session.add(emp)
            session.flush()
            emp_id_map[e["id"]] = emp.id
            print(f"  [OK] Employee: {emp.name}")

        session.commit()

        # ── Attendance ─────────────────────────────────────────────────────
        att_count = 0
        for a in data.get("attendance", []):
            emp_pk = emp_id_map.get(a.get("employeeId"))
            if not emp_pk:
                continue
            existing = session.exec(
                select(Attendance)
                .where(Attendance.employee_id == emp_pk)
                .where(Attendance.date == a.get("date"))
            ).first()
            if existing:
                continue
            session.add(Attendance(
                legacy_id=a.get("id"),
                employee_id=emp_pk,
                date=a.get("date", ""),
                status=a.get("status", "Present"),
            ))
            att_count += 1

        session.commit()
        print(f"  [OK] Attendance records: {att_count}")

        # ── Leaves ─────────────────────────────────────────────────────────
        leave_count = 0
        for l in data.get("leaves", []):
            emp_pk = emp_id_map.get(l.get("employeeId"))
            if not emp_pk:
                continue
            session.add(Leave(
                legacy_id=l.get("id"),
                employee_id=emp_pk,
                from_date=l.get("fromDate", ""),
                to_date=l.get("toDate", ""),
                type=l.get("type", "Casual Leave"),
                reason=l.get("reason", ""),
                status=l.get("status", "Pending"),
                requested_on=l.get("requestedOn", ""),
            ))
            leave_count += 1

        session.commit()
        print(f"  [OK] Leave records: {leave_count}")

        # ── Performance Reviews ────────────────────────────────────────────
        perf_count = 0
        for p in data.get("performance", []):
            emp_pk = emp_id_map.get(p.get("employeeId"))
            if not emp_pk:
                continue
            session.add(PerformanceReview(
                legacy_id=p.get("id"),
                employee_id=emp_pk,
                rating=float(p.get("rating", 0)),
                feedback=p.get("feedback", ""),
                ai_summary=p.get("aiSummary", ""),
            ))
            perf_count += 1

        session.commit()
        print(f"  [OK] Performance reviews: {perf_count}")

    print("\n[DONE] Seeding complete! All data is now in Neon PostgreSQL.")


if __name__ == "__main__":
    seed()
