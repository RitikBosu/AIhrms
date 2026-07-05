from fastapi import Header, HTTPException, status
from app.services.auth_utils import verify_token
from app.database import get_session
from app.models import User
from sqlmodel import Session
from fastapi import Depends


def get_current_user(authorization: str = Header(None), session: Session = Depends(get_session)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please login again.")
    token = authorization.replace("Bearer ", "")
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired, please login again.")
        
    db_user = session.get(User, user.get("id"))
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account no longer exists.")
        
    return user
