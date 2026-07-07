"""
Deterministic Compliance Validator for AI-Generated Rosters.

Design principle: the LLM (Groq / Llama 3) proposes a draft schedule.
It is NEVER trusted to enforce labor law or business rules by itself.
This module re-checks every proposed shift deterministically before
anything is written to the database or shown to a manager for approval.

Flow:
    ai_output = call_groq(prompt, context)          # untrusted draft
    result = validate_roster(ai_output, employees, availability, leaves, existing_shifts)
    if result.blocking_violations:
        # do NOT save; return violations to the frontend for manager review
    else:
        # safe to present result.approved_shifts for manager "Publish" step
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


# ─── Violation Types ──────────────────────────────────────────────────────────

class ViolationType(str, Enum):
    OVERTIME = "overtime"
    DOUBLE_BOOKED = "double_booked"
    UNAVAILABLE = "unavailable"
    ON_LEAVE = "on_leave"
    OVERLAPS_EXISTING = "overlaps_existing_shift"
    NEGATIVE_DURATION = "negative_duration"


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class Violation:
    """A single compliance violation. Used by the frontend to highlight issues."""
    type: ViolationType
    employee_id: int
    detail: str
    shift_index: int          # index into the proposed shifts list, for UI highlighting
    blocking: bool            # True = must be fixed before save; False = warn only


@dataclass
class ProposedShift:
    """A single shift proposed by the AI (or manual entry)."""
    employee_id: int
    start_time: datetime
    end_time: datetime
    title: str = ""


@dataclass
class EmployeeConstraints:
    """Minimal employee info needed for validation."""
    id: int
    max_weekly_hours: int


@dataclass
class AvailabilityWindow:
    """One recurring availability slot for an employee."""
    employee_id: int
    day_of_week: int          # 0=Monday ... 6=Sunday
    start_time: str           # "09:00"
    end_time: str             # "17:00"
    is_available: bool = True


@dataclass
class LeaveRecord:
    """An approved leave period for an employee."""
    employee_id: int
    start_date: datetime
    end_date: datetime


@dataclass
class ExistingShift:
    """A shift already committed to the database."""
    employee_id: int
    start_time: datetime
    end_time: datetime


@dataclass
class ValidationResult:
    """Container for validated shifts and any violations found."""
    approved_shifts: List[ProposedShift]
    violations: List[Violation] = field(default_factory=list)

    @property
    def blocking_violations(self) -> List[Violation]:
        return [v for v in self.violations if v.blocking]

    @property
    def is_clean(self) -> bool:
        return len(self.blocking_violations) == 0


# ─── Helper Functions ─────────────────────────────────────────────────────────

def _hours_between(start: datetime, end: datetime) -> float:
    """Calculate hours between two datetimes, flooring at 0."""
    return max(0.0, (end - start).total_seconds() / 3600.0)


def _parse_hhmm(value: str) -> int:
    """Convert 'HH:MM' to minutes-since-midnight for easy comparison."""
    h, m = value.split(":")
    return int(h) * 60 + int(m)


def _within_availability(shift: ProposedShift, windows: List[AvailabilityWindow]) -> bool:
    """Check if a shift falls inside any of the employee's availability windows for that day."""
    day = shift.start_time.weekday()
    day_windows = [
        w for w in windows
        if w.employee_id == shift.employee_id and w.day_of_week == day
    ]

    # No availability record for that day = treat as unavailable.
    # This is the safer default; salaried employees (who have no availability
    # records) should never be fed into the AI scheduler in the first place.
    if not day_windows:
        return False

    shift_start_min = shift.start_time.hour * 60 + shift.start_time.minute
    shift_end_min = shift.end_time.hour * 60 + shift.end_time.minute

    for w in day_windows:
        if not w.is_available:
            continue
        if _parse_hhmm(w.start_time) <= shift_start_min and shift_end_min <= _parse_hhmm(w.end_time):
            return True
    return False


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """Check if two time ranges overlap."""
    return a_start < b_end and b_start < a_end


# ─── Main Validator ───────────────────────────────────────────────────────────

def validate_roster(
    proposed_shifts: List[ProposedShift],
    employees: Dict[int, EmployeeConstraints],
    availability: List[AvailabilityWindow],
    leaves: List[LeaveRecord],
    existing_shifts: List[ExistingShift],
) -> ValidationResult:
    """
    Deterministically validate an AI-proposed roster.

    Returns a ValidationResult listing every violation found. Callers should
    refuse to persist a roster with any blocking=True violation and instead
    surface it to the manager (or re-prompt the AI with the violation as
    feedback for a second attempt).
    """
    violations: List[Violation] = []

    # Track running weekly hours per employee, seeded with hours
    # already scheduled in existing_shifts for the relevant period.
    weekly_hours: Dict[int, float] = {}
    for ex in existing_shifts:
        weekly_hours[ex.employee_id] = weekly_hours.get(ex.employee_id, 0.0) + _hours_between(
            ex.start_time, ex.end_time
        )

    for idx, shift in enumerate(proposed_shifts):
        emp = employees.get(shift.employee_id)

        # ── Basic sanity ──
        if shift.end_time <= shift.start_time:
            violations.append(Violation(
                type=ViolationType.NEGATIVE_DURATION,
                employee_id=shift.employee_id,
                detail=f"Shift end ({shift.end_time}) is not after start ({shift.start_time}).",
                shift_index=idx,
                blocking=True,
            ))
            continue  # skip further checks on a malformed shift

        # ── Leave check ──
        on_leave = any(
            lv.employee_id == shift.employee_id
            and lv.start_date <= shift.start_time <= lv.end_date
            for lv in leaves
        )
        if on_leave:
            violations.append(Violation(
                type=ViolationType.ON_LEAVE,
                employee_id=shift.employee_id,
                detail="Employee has an approved leave covering this shift.",
                shift_index=idx,
                blocking=True,
            ))

        # ── Availability check ──
        if not _within_availability(shift, availability):
            violations.append(Violation(
                type=ViolationType.UNAVAILABLE,
                employee_id=shift.employee_id,
                detail="Shift falls outside the employee's stated availability window.",
                shift_index=idx,
                blocking=True,
            ))

        # ── Double-booking against existing DB shifts ──
        for ex in existing_shifts:
            if ex.employee_id == shift.employee_id and _overlaps(
                shift.start_time, shift.end_time, ex.start_time, ex.end_time
            ):
                violations.append(Violation(
                    type=ViolationType.OVERLAPS_EXISTING,
                    employee_id=shift.employee_id,
                    detail=f"Overlaps an existing shift ({ex.start_time} – {ex.end_time}).",
                    shift_index=idx,
                    blocking=True,
                ))

        # ── Double-booking within the proposed batch itself ──
        for other_idx, other in enumerate(proposed_shifts):
            if other_idx <= idx:
                continue
            if other.employee_id == shift.employee_id and _overlaps(
                shift.start_time, shift.end_time, other.start_time, other.end_time
            ):
                violations.append(Violation(
                    type=ViolationType.DOUBLE_BOOKED,
                    employee_id=shift.employee_id,
                    detail=f"Two proposed shifts overlap for this employee (indices {idx} and {other_idx}).",
                    shift_index=idx,
                    blocking=True,
                ))

        # ── Overtime check ──
        shift_hours = _hours_between(shift.start_time, shift.end_time)
        weekly_hours[shift.employee_id] = weekly_hours.get(shift.employee_id, 0.0) + shift_hours

        if emp is None:
            violations.append(Violation(
                type=ViolationType.OVERTIME,
                employee_id=shift.employee_id,
                detail="Unknown employee_id — cannot verify max_weekly_hours; treat as blocking.",
                shift_index=idx,
                blocking=True,
            ))
        elif weekly_hours[shift.employee_id] > emp.max_weekly_hours:
            violations.append(Violation(
                type=ViolationType.OVERTIME,
                employee_id=shift.employee_id,
                detail=(
                    f"Running weekly total {weekly_hours[shift.employee_id]:.1f}h exceeds "
                    f"limit of {emp.max_weekly_hours}h after this shift."
                ),
                shift_index=idx,
                blocking=True,
            ))

    return ValidationResult(approved_shifts=proposed_shifts, violations=violations)
