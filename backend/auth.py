import os
from datetime import datetime, timedelta
from typing import Optional, List, Callable, Dict

from fastapi import HTTPException, Depends, Header
from jose import jwt, JWTError
import hashlib
from bson import ObjectId

try:
    from backend.mongo import get_collection
except Exception:
    from .mongo import get_collection


# Env-configurable JWT settings (dev defaults)
JWT_SECRET = os.getenv('JWT_SECRET', 'super-secret-key-change-me')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '60'))

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hashlib.sha256(plain.encode()).hexdigest() == hashed


def create_access_token(user_id: str, role: str, extra: Optional[Dict] = None) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user_id, "role": role, "exp": expire}
    if extra:
        to_encode.update(extra)
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Extract Bearer token, validate JWT, and fetch user from MongoDB."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token")
        users = get_collection('users')
        if users is None:
            # Fallback: return user details from token claims when DB is unavailable
            return {
                "id": sub,
                "name": payload.get("name"),
                "email": payload.get("email"),
                "role": payload.get("role", "student"),
            }
        doc = users.find_one({"_id": ObjectId(sub)})
        if not doc:
            raise HTTPException(status_code=401, detail="User not found")
        return {
            "id": str(doc["_id"]),
            "name": doc.get("name"),
            "email": doc.get("email"),
            "role": doc.get("role", "student"),
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Token validation failed")


def require_roles(roles: List[str]) -> Callable:
    """Dependency factory for role-based access control."""
    async def dep(user = Depends(get_current_user)):
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Forbidden: insufficient role")
        return user
    return dep