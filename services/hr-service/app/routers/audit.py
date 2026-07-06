from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from app.database import get_session
from app.models import AuditLog, User
from app.routers.deps import get_current_user

router = APIRouter()

@router.get("/audit")
def get_audit_logs(skip: int = 0, limit: int = 100, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can view audit logs.")
    
    logs = session.exec(select(AuditLog).order_by(AuditLog.id.desc()).offset(skip).limit(limit)).all()
    
    # Resolve usernames
    result = []
    for log in logs:
        u = session.get(User, log.user_id)
        result.append({
            "id": log.id,
            "userId": log.user_id,
            "username": u.username if u else "Unknown",
            "action": log.action,
            "targetId": log.target_id,
            "details": log.details,
            "timestamp": log.timestamp
        })
    return result
