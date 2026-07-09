from typing import Optional, List
from datetime import date, datetime
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import DateTime
import sqlalchemy as sa
import enum


# ─── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    action: str
    target_id: str
    details: str
    timestamp: str


# ─── User ────────────────────────────────────────────────────────────────────

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    legacy_id: Optional[str] = Field(default=None, index=True)   # keeps old string IDs from db.json
    username: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    role: str = Field(default="employee")   # admin | hr | manager | employee


# ─── Employment Type Enum ─────────────────────────────────────────────────────

class EmploymentType(str, enum.Enum):
    SALARIED = "SALARIED"
    SHIFT = "SHIFT"


# ─── Employee ────────────────────────────────────────────────────────────────

class Employee(SQLModel, table=True):
    __tablename__ = "employees"

    id: Optional[int] = Field(default=None, primary_key=True)
    legacy_id: Optional[str] = Field(default=None, index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    user_legacy_id: Optional[str] = Field(default=None)           # for cross-referencing seeded data
    name: str
    email: str
    department: str
    designation: str
    salary: float
    joining_date: Optional[str] = Field(default=None)
    is_deleted: bool = Field(default=False)
    # Phase 5: Shift scheduling fields
    employment_type: Optional[str] = Field(default=EmploymentType.SALARIED.value)
    max_weekly_hours: int = Field(default=40)
    # Phase 7: PTO balances
    pto_balance_days: float = Field(default=20.0)
    sick_leave_balance_days: float = Field(default=10.0)


# ─── Attendance ───────────────────────────────────────────────────────────────

class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"

    id: Optional[int] = Field(default=None, primary_key=True)
    legacy_id: Optional[str] = Field(default=None, index=True)
    employee_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    employee_legacy_id: Optional[str] = Field(default=None)
    date: str
    status: str   # Present | Absent
    # Phase 5: Precise time tracking
    clock_in: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    clock_out: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    ip_address: Optional[str] = Field(default=None)


# ─── Leave ────────────────────────────────────────────────────────────────────

class Leave(SQLModel, table=True):
    __tablename__ = "leaves"

    id: Optional[int] = Field(default=None, primary_key=True)
    legacy_id: Optional[str] = Field(default=None, index=True)
    employee_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    employee_legacy_id: Optional[str] = Field(default=None)
    from_date: str
    to_date: str
    type: str
    reason: str
    status: str = Field(default="Pending")   # Pending | Approved | Rejected
    requested_on: Optional[str] = Field(default=None)
    ai_justification: Optional[str] = Field(default=None)


# ─── Performance Review ───────────────────────────────────────────────────────

class PerformanceReview(SQLModel, table=True):
    __tablename__ = "performance_reviews"

    id: Optional[int] = Field(default=None, primary_key=True)
    legacy_id: Optional[str] = Field(default=None, index=True)
    employee_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    employee_legacy_id: Optional[str] = Field(default=None)
    rating: float
    feedback: str
    ai_summary: Optional[str] = Field(default=None)
