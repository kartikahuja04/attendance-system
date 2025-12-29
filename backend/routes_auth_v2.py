"""
Authentication API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from datetime import datetime
from backend.database import db, serialize_doc, serialize_docs
from schemas import (
    LoginRequest,
    LoginResponse,
    UserResponse,
    UserCreate,
    RoleEnum,
)
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=dict)
async def register(
    request: Request,
    user_data: UserCreate,
    org_code: str = None,
):
    """Register a new user"""
    try:
        # Validate input
        if not user_data.email or not user_data.password or not user_data.full_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email, password, and full name are required",
            )

        users_collection = db["users"]
        
        # Check if user already exists
        if users_collection.find_one({"email": user_data.email}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Get organization
        org = None
        if org_code:
            orgs_collection = db["organizations"]
            org = orgs_collection.find_one({"code": org_code})
            if not org:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found",
                )
        else:
            # For super admin registration, no org required
            if user_data.role != RoleEnum.SUPER_ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization code required for non-super-admin users",
                )

        # Create new user
        new_user = {
            "email": user_data.email,
            "full_name": user_data.full_name,
            "password_hash": hash_password(user_data.password),
            "role": user_data.role,
            "organization_id": str(org["_id"]) if org else None,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = users_collection.insert_one(new_user)
        new_user["_id"] = str(result.inserted_id)

        # Log registration
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": str(result.inserted_id),
            "action": "register",
            "resource": "user",
            "resource_id": str(result.inserted_id),
            "organization_id": new_user["organization_id"],
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {
            "message": "User registered successfully",
            "user_id": str(result.inserted_id),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, credentials: LoginRequest):
    """Login user and return JWT token"""
    try:
        users_collection = db["users"]
        
        # Find user by email
        user = users_collection.find_one({"email": credentials.email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Check if user is active
        if not user.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )

        # Verify password
        if not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Create JWT token
        access_token = create_access_token(
            user_id=str(user["_id"]),
            email=user["email"],
            role=user["role"],
            organization_id=user.get("organization_id", ""),
        )

        # Log login
        login_history = db["login_history"]
        login_history.insert_one({
            "user_id": str(user["_id"]),
            "email": user["email"],
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "created_at": datetime.utcnow(),
        })

        return LoginResponse(
            access_token=access_token,
            user=UserResponse(
                id=str(user["_id"]),
                email=user["email"],
                full_name=user["full_name"],
                role=user["role"],
                organization_id=user.get("organization_id", ""),
                is_active=user["is_active"],
                created_at=user["created_at"],
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    try:
        users_collection = db["users"]
        user = users_collection.find_one({"_id": current_user["user_id"]})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            organization_id=user.get("organization_id", ""),
            is_active=user["is_active"],
            created_at=user["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile",
        )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (client-side token deletion)"""
    return {"message": "Logged out successfully"}
