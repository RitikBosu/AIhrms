"""
Phase 5: Shift Scheduling Models

- Shift: Represents a single scheduled work period for one employee.
- Availability: Recurring weekly time windows when an employee is available.
- ShiftSwapRequest: Bilateral swap requests between two employees, requiring
  manager approval.
"""
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import DateTime


# ─── Shift ────────────────────────────────────────────────────────────────────

class Shift(SQLModel, table=True):
    __tablename__ = "shifts"

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employees.id")
    title: str                          # e.g., "Morning Shift", "Closing"
    start_time: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    end_time: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    status: str = Field(default="Scheduled")  # Scheduled | Completed | SwapRequested
    created_by: Optional[int] = Field(default=None)  # user_id of whoever published
    is_ai_generated: bool = Field(default=False)


# ─── Availability ─────────────────────────────────────────────────────────────

class Availability(SQLModel, table=True):
    __tablename__ = "availability"

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employees.id")
    day_of_week: int                    # 0=Monday ... 6=Sunday
    start_time: str                     # "09:00" (HH:MM)
    end_time: str                       # "17:00" (HH:MM)
    is_available: bool = Field(default=True)


# ─── Shift Swap Request ───────────────────────────────────────────────────────

class ShiftSwapRequest(SQLModel, table=True):
    __tablename__ = "shift_swap_requests"

    id: Optional[int] = Field(default=None, primary_key=True)
    shift_id: int = Field(foreign_key="shifts.id")
    requester_id: int = Field(foreign_key="employees.id")   # the employee offering their shift
    target_id: int = Field(foreign_key="employees.id")       # the coworker being asked to cover
    status: str = Field(default="Pending")  # Pending | AcceptedByTarget | Approved | Rejected
    created_at: Optional[str] = Field(default=None)
    resolved_at: Optional[str] = Field(default=None)
    resolved_by: Optional[int] = Field(default=None)         # manager user_id who approved/rejected
