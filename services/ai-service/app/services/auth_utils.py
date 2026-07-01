import os
from jose import jwt

TOKEN_SECRET = os.environ.get("TOKEN_SECRET", "fwc-demo-secret-change-before-production")


def verify_token(token: str):
    try:
        return jwt.decode(token, TOKEN_SECRET, algorithms=["HS256"])
    except Exception:
        return None
