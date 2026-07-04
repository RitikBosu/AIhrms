import time
import os
from fastapi import HTTPException, status

def create_id(prefix: str) -> str:
    return f"{prefix}-{int(time.time()*1000)}-{os.urandom(3).hex()}"

def require_role(user: dict, allowed_roles: list) -> None:
    if user.get("role") not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission for this action.")

def get_employee_for_user(db: dict, user_id: str) -> dict:
    for emp in db.get("employees", []):
        if emp.get("userId") == user_id:
            return emp
    return None
