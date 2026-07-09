from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import requests

from app.database import get_session
from app.models import Employee, User
from app.models.shifts import Shift, Availability, ShiftSwapRequest, ShiftBid
from app.routers.deps import get_current_user

router = APIRouter()


def require_role(user, allowed_roles):
    if user["role"] not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have permission for this action."
        )


def _get_emp_for_user(session: Session, user_id: int) -> Optional[Employee]:
    return session.exec(select(Employee).where(Employee.user_id == user_id)).first()


# ─── Shifts CRUD ──────────────────────────────────────────────────────────────

@router.get("/shifts")
def get_shifts(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    session: Session = Depends(get_session), 
    user: dict = Depends(get_current_user)
):
    query = select(Shift)
    # If employee, only see their own shifts. Admin/Manager/HR see all.
    if user["role"] == "employee":
        emp = _get_emp_for_user(session, user["id"])
        if not emp:
            return []
        query = query.where(Shift.employee_id == emp.id)
    
    if start_date:
        query = query.where(Shift.start_time >= start_date)
    if end_date:
        query = query.where(Shift.end_time <= end_date)
        
    return session.exec(query).all()


@router.post("/shifts", status_code=status.HTTP_201_CREATED)
def create_shift(shift: Shift, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_role(user, ["admin", "hr", "manager"])
    shift.created_by = user["id"]
    
    # We could theoretically call validate_roster here for manual entries,
    # but for MVP, manual entry assumes the manager knows what they are doing.
    
    session.add(shift)
    session.commit()
    session.refresh(shift)
    return shift


# ─── Availability ─────────────────────────────────────────────────────────────

@router.get("/availability")
def get_availability(employee_id: Optional[int] = None, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    query = select(Availability)
    if user["role"] == "employee":
        emp = _get_emp_for_user(session, user["id"])
        if not emp:
            return []
        query = query.where(Availability.employee_id == emp.id)
    elif employee_id:
        query = query.where(Availability.employee_id == employee_id)
        
    return session.exec(query).all()


@router.post("/availability", status_code=status.HTTP_201_CREATED)
def create_availability(avail: Availability, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    # Employees can set their own availability. Managers can set for others.
    if user["role"] == "employee":
        emp = _get_emp_for_user(session, user["id"])
        if not emp or avail.employee_id != emp.id:
            raise HTTPException(status_code=403, detail="Can only set your own availability")
    else:
        require_role(user, ["admin", "hr", "manager"])
        
    session.add(avail)
    session.commit()
    session.refresh(avail)
    return avail


# ─── Shift Swaps ──────────────────────────────────────────────────────────────

class SwapRequestPayload(BaseModel):
    shift_id: int
    target_id: int


@router.post("/swaps")
def request_swap(payload: SwapRequestPayload, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    emp = _get_emp_for_user(session, user["id"])
    if not emp:
        raise HTTPException(status_code=404, detail="Employee record not found")
        
    shift = session.get(Shift, payload.shift_id)
    if not shift or shift.employee_id != emp.id:
        raise HTTPException(status_code=404, detail="Shift not found or doesn't belong to you")
        
    target = session.get(Employee, payload.target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target employee not found")
        
    swap = ShiftSwapRequest(
        shift_id=shift.id,
        requester_id=emp.id,
        target_id=target.id,
        created_at=datetime.utcnow().isoformat()
    )
    
    shift.status = "SwapRequested"
    
    session.add(swap)
    session.add(shift)
    session.commit()
    session.refresh(swap)
    
    # Fire Webhook (Fire-and-forget MVP)
    # send_webhook("swap.requested", {"swap_id": swap.id, "requester": emp.name, "target": target.name})
    
    return swap


@router.put("/swaps/{swap_id}/resolve")
def resolve_swap(swap_id: int, action: str, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    # action: "accept" (by target), "approve" (by manager), "reject"
    swap = session.get(ShiftSwapRequest, swap_id)
    if not swap:
        raise HTTPException(status_code=404, detail="Swap request not found")
        
    shift = session.get(Shift, swap.shift_id)
    
    if action == "accept":
        # Only target can accept
        emp = _get_emp_for_user(session, user["id"])
        if not emp or swap.target_id != emp.id:
            raise HTTPException(status_code=403, detail="Only target can accept")
        swap.status = "AcceptedByTarget"
        
    elif action in ["approve", "reject"]:
        require_role(user, ["admin", "manager", "hr"])
        swap.status = "Approved" if action == "approve" else "Rejected"
        swap.resolved_at = datetime.utcnow().isoformat()
        swap.resolved_by = user["id"]
        
        if action == "approve":
            # Reassign shift
            shift.employee_id = swap.target_id
            shift.status = "Scheduled"
        else:
            shift.status = "Scheduled" # Revert to normal
            
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    session.add(swap)
    session.add(shift)
    session.commit()
    
    return swap


# ─── Open Shifts Marketplace ──────────────────────────────────────────────────

@router.get("/open-shifts")
def get_open_shifts(session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    # Returns all shifts where employee_id is null
    query = select(Shift).where(Shift.employee_id == None)
    return session.exec(query).all()


class OpenShiftPayload(BaseModel):
    title: str
    start_time: str
    end_time: str


@router.post("/open-shifts", status_code=status.HTTP_201_CREATED)
def create_open_shift(payload: OpenShiftPayload, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_role(user, ["admin", "hr", "manager"])
    try:
        st = datetime.fromisoformat(payload.start_time.replace("Z", "+00:00"))
        et = datetime.fromisoformat(payload.end_time.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    shift = Shift(
        employee_id=None,
        title=payload.title,
        start_time=st,
        end_time=et,
        status="Open",
        created_by=user["id"]
    )
    session.add(shift)
    session.commit()
    session.refresh(shift)
    return shift


@router.post("/open-shifts/{shift_id}/bid", status_code=status.HTTP_201_CREATED)
def bid_on_open_shift(shift_id: int, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    if user["role"] != "employee":
        raise HTTPException(status_code=403, detail="Only employees can bid on open shifts")

    emp = _get_emp_for_user(session, user["id"])
    if not emp:
        raise HTTPException(status_code=404, detail="Employee record not found")

    shift = session.get(Shift, shift_id)
    if not shift or shift.employee_id is not None:
        raise HTTPException(status_code=404, detail="Open shift not found or already assigned")

    # Check if already bid
    existing_bid = session.exec(select(ShiftBid).where(ShiftBid.shift_id == shift_id).where(ShiftBid.employee_id == emp.id)).first()
    if existing_bid:
        raise HTTPException(status_code=400, detail="You have already bid on this shift")

    bid = ShiftBid(
        shift_id=shift_id,
        employee_id=emp.id,
        created_at=datetime.utcnow().isoformat()
    )
    session.add(bid)
    session.commit()
    session.refresh(bid)
    return bid


@router.get("/open-shifts/{shift_id}/bids")
def get_open_shift_bids(shift_id: int, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_role(user, ["admin", "manager", "hr"])
    
    # We want to return the bids along with the employee details
    bids = session.exec(select(ShiftBid).where(ShiftBid.shift_id == shift_id)).all()
    
    results = []
    for b in bids:
        emp = session.get(Employee, b.employee_id)
        if emp:
            results.append({
                "id": b.id,
                "shift_id": b.shift_id,
                "employee_id": b.employee_id,
                "status": b.status,
                "created_at": b.created_at,
                "employee": {
                    "id": emp.id,
                    "name": emp.name,
                    "department": emp.department,
                    "max_weekly_hours": emp.max_weekly_hours,
                    "performance_rating": emp.performance_rating
                }
            })
    return results


@router.post("/open-shifts/bids/{bid_id}/approve")
def approve_shift_bid(bid_id: int, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_role(user, ["admin", "manager", "hr"])
    
    bid = session.get(ShiftBid, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
        
    shift = session.get(Shift, bid.shift_id)
    if not shift or shift.employee_id is not None:
        raise HTTPException(status_code=400, detail="Shift no longer open")
        
    # Assign shift
    shift.employee_id = bid.employee_id
    shift.status = "Scheduled"
    
    # Approve this bid
    bid.status = "Approved"
    
    # Reject all other bids for this shift
    other_bids = session.exec(select(ShiftBid).where(ShiftBid.shift_id == bid.shift_id).where(ShiftBid.id != bid.id)).all()
    for ob in other_bids:
        ob.status = "Rejected"
        session.add(ob)
        
    session.add(shift)
    session.add(bid)
    session.commit()
    
    return {"message": "Bid approved, shift assigned", "shift_id": shift.id, "employee_id": shift.employee_id}

