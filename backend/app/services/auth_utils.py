import os
import time
import hashlib
from jose import jwt

TOKEN_SECRET = os.environ.get("TOKEN_SECRET", "fwc-demo-secret-change-before-production")

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, original_hash = stored_hash.split(":")
        new_hash = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1, maxmem=0, dklen=64).hex()
        return original_hash == new_hash
    except Exception:
        return False

def sign_token(user: dict) -> str:
    payload = {
        "id": user["id"],
        "role": user["role"],
        "name": user["name"],
        "exp": int(time.time()) + 60 * 60 * 6
    }
    return jwt.encode(payload, TOKEN_SECRET, algorithm="HS256")

def verify_token(token: str):
    try:
        return jwt.decode(token, TOKEN_SECRET, algorithms=["HS256"])
    except Exception:
        return None
