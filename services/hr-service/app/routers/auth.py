from fastapi import APIRouter, HTTPException, status, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
from sqlmodel import Session, select
from pydantic import BaseModel

from app.database import get_session
from app.models import User
from app.services.auth_utils import verify_password, sign_token

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, login_req: LoginRequest, session: Session = Depends(get_session)):
    email = login_req.email.lower().strip()
    user = session.exec(select(User).where(User.email == email)).first()

    if not user or not verify_password(login_req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = sign_token(user_id=user.id, role=user.role, name=user.username)
    return {
        "token": token,
        "user": {
            "id": user.id,
            "name": user.username,
            "email": user.email,
            "role": user.role
        }
    }
