from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.services.db import read_db
from app.services.auth_utils import verify_password, sign_token

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
def login(request: LoginRequest):
    db = read_db()
    email = request.email.lower()
    user = next((u for u in db.get("users", []) if u.get("email", "").lower() == email), None)
    if not user or not verify_password(request.password, user.get("passwordHash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    
    public_user = {k: v for k, v in user.items() if k != "passwordHash"}
    return {"token": sign_token(user), "user": public_user}
