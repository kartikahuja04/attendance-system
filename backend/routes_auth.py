from fastapi import APIRouter
from mongo import db
from jwt_utils import create_access_token

router = APIRouter()

users_collection = db["users"]


@router.post("/login")
def login(data: dict):
    user = users_collection.find_one({
        "email": data["email"],
        "password": data["password"]
    })

    if not user:
        return {"success": False, "message": "Invalid credentials"}

    token = create_access_token({
        "user_id": str(user["_id"]),
        "email": user["email"],
        "role": user["role"]
    })

    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "name": user["name"],
            "role": user["role"]
        }
    }
