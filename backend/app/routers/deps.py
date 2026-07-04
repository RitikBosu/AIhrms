from fastapi import Header, HTTPException, status
from app.services.auth_utils import verify_token
from app.services.db import read_db

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please login again.")
    token = authorization.replace("Bearer ", "")
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please login again.")
        
    db = read_db()
    db_user = next((u for u in db.get("users", []) if u.get("id") == user.get("id")), None)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account no longer exists.")
        
    return user
