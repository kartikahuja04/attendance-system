"""
Organization management API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from datetime import datetime
from backend.database import db, serialize_doc, serialize_docs
from bson import ObjectId
from schemas import OrganizationCreate, OrganizationResponse, RoleEnum
from auth import get_current_user
from permissions import require_role, PermissionEnum, has_permission
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/organizations", response_model=dict)
async def create_organization(
    org_data: OrganizationCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Create a new organization (Super Admin only)"""
    try:
        # Check permission
        if current_user["role"] != RoleEnum.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admin can create organizations",
            )

        orgs_collection = db["organizations"]

        # Check if organization code already exists
        if orgs_collection.find_one({"code": org_data.code}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization code already exists",
            )

        # Create organization
        new_org = {
            "name": org_data.name,
            "code": org_data.code,
            "email": org_data.email,
            "phone": org_data.phone,
            "address": org_data.address,
            "created_by": current_user["user_id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
        }

        result = orgs_collection.insert_one(new_org)
        org_id = str(result.inserted_id)

        # Create organization settings
        settings_collection = db["organization_settings"]
        settings_collection.insert_one({
            "organization_id": org_id,
            "allow_faculty_edit_attendance": True,
            "edit_attendance_window_hours": 24,
            "allow_backdated_marking": True,
            "max_backdated_days": 7,
            "allow_student_view_attendance": True,
            "created_at": datetime.utcnow(),
        })

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "create_organization",
            "resource": "organization",
            "resource_id": org_id,
            "organization_id": org_id,
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {
            "message": "Organization created successfully",
            "organization_id": org_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create organization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization",
        )


@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get organization details"""
    try:
        # Check if user belongs to organization
        if current_user["role"] != RoleEnum.SUPER_ADMIN:
            if current_user["organization_id"] != org_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied",
                )

        orgs_collection = db["organizations"]
        org = orgs_collection.find_one({"_id": ObjectId(org_id)})

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        return OrganizationResponse(
            id=str(org["_id"]),
            name=org["name"],
            code=org["code"],
            email=org["email"],
            phone=org.get("phone"),
            address=org.get("address"),
            created_at=org["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get organization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch organization",
        )


@router.put("/organizations/{org_id}")
async def update_organization(
    org_id: str,
    org_data: OrganizationCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Update organization details"""
    try:
        # Check permission
        if current_user["role"] == RoleEnum.ORG_ADMIN:
            if current_user["organization_id"] != org_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied",
                )
        elif current_user["role"] != RoleEnum.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        orgs_collection = db["organizations"]
        update_data = {
            "name": org_data.name,
            "email": org_data.email,
            "phone": org_data.phone,
            "address": org_data.address,
            "updated_at": datetime.utcnow(),
        }

        result = orgs_collection.update_one(
            {"_id": ObjectId(org_id)},
            {"$set": update_data},
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "update_organization",
            "resource": "organization",
            "resource_id": org_id,
            "organization_id": current_user["organization_id"],
            "changes": update_data,
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {"message": "Organization updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update organization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization",
        )
