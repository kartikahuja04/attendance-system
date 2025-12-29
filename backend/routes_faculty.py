"""
Faculty management API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from datetime import datetime
from backend.database import db, serialize_doc, serialize_docs
from bson import ObjectId
from schemas import FacultyCreate, FacultyResponse, RoleEnum
from auth import get_current_user, hash_password
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/faculty", response_model=dict)
async def create_faculty(
    faculty_data: FacultyCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Create a new faculty member (Admin only)"""
    try:
        # Check permission
        if current_user["role"] not in [RoleEnum.ORG_ADMIN, RoleEnum.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create faculty",
            )

        org_id = current_user["organization_id"]
        faculty_collection = db["faculty"]
        users_collection = db["users"]

        # Check if faculty with same employee_id exists
        if faculty_collection.find_one({
            "organization_id": org_id,
            "employee_id": faculty_data.employee_id,
        }):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID already exists in this organization",
            )

        # Check if email exists
        if users_collection.find_one({"email": faculty_data.email}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create user account for faculty
        user_data = {
            "email": faculty_data.email,
            "full_name": faculty_data.full_name,
            "password_hash": hash_password("default123"),
            "role": RoleEnum.FACULTY,
            "organization_id": org_id,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        user_result = users_collection.insert_one(user_data)
        user_id = str(user_result.inserted_id)

        # Create faculty record
        faculty_record = {
            "user_id": user_id,
            "organization_id": org_id,
            "email": faculty_data.email,
            "full_name": faculty_data.full_name,
            "employee_id": faculty_data.employee_id,
            "department": faculty_data.department,
            "created_by": current_user["user_id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "subjects": [],  # Will be populated when assigning subjects
            "timetables": [],  # Will be populated when creating timetables
        }

        faculty_result = faculty_collection.insert_one(faculty_record)
        faculty_id = str(faculty_result.inserted_id)

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "create_faculty",
            "resource": "faculty",
            "resource_id": faculty_id,
            "organization_id": org_id,
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {
            "message": "Faculty created successfully",
            "faculty_id": faculty_id,
            "user_id": user_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create faculty error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create faculty",
        )


@router.get("/faculty", response_model=dict)
async def list_faculty(
    department: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    current_user: dict = Depends(get_current_user),
):
    """List faculty in organization"""
    try:
        # Only admins can view full list
        if current_user["role"] not in [RoleEnum.ORG_ADMIN, RoleEnum.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        org_id = current_user["organization_id"]
        faculty_collection = db["faculty"]

        # Build filter
        filter_dict = {"organization_id": org_id, "is_active": True}
        if department:
            filter_dict["department"] = department

        # Get total count
        total = faculty_collection.count_documents(filter_dict)

        # Get paginated results
        faculty_list = list(faculty_collection.find(filter_dict).skip(skip).limit(limit))

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "faculty": serialize_docs(faculty_list),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List faculty error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch faculty",
        )


@router.get("/faculty/{faculty_id}", response_model=FacultyResponse)
async def get_faculty(
    faculty_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get faculty details"""
    try:
        org_id = current_user["organization_id"]
        faculty_collection = db["faculty"]

        faculty = faculty_collection.find_one({
            "_id": ObjectId(faculty_id),
            "organization_id": org_id,
        })

        if not faculty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Faculty not found",
            )

        return FacultyResponse(
            id=str(faculty["_id"]),
            email=faculty["email"],
            full_name=faculty["full_name"],
            employee_id=faculty["employee_id"],
            department=faculty["department"],
            organization_id=org_id,
            created_at=faculty["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get faculty error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch faculty",
        )


@router.put("/faculty/{faculty_id}")
async def update_faculty(
    faculty_id: str,
    faculty_data: FacultyCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Update faculty details"""
    try:
        # Only admins can edit faculty
        if current_user["role"] not in [RoleEnum.ORG_ADMIN, RoleEnum.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        org_id = current_user["organization_id"]
        faculty_collection = db["faculty"]
        users_collection = db["users"]

        faculty = faculty_collection.find_one({
            "_id": ObjectId(faculty_id),
            "organization_id": org_id,
        })

        if not faculty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Faculty not found",
            )

        # Update faculty record
        update_data = {
            "full_name": faculty_data.full_name,
            "department": faculty_data.department,
            "updated_at": datetime.utcnow(),
        }

        faculty_collection.update_one(
            {"_id": ObjectId(faculty_id)},
            {"$set": update_data},
        )

        # Update user record
        users_collection.update_one(
            {"_id": ObjectId(faculty["user_id"])},
            {"$set": {"full_name": faculty_data.full_name, "updated_at": datetime.utcnow()}},
        )

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "update_faculty",
            "resource": "faculty",
            "resource_id": faculty_id,
            "organization_id": org_id,
            "changes": update_data,
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {"message": "Faculty updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update faculty error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update faculty",
        )


@router.delete("/faculty/{faculty_id}")
async def delete_faculty(
    faculty_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Soft delete faculty"""
    try:
        # Only admins can delete faculty
        if current_user["role"] not in [RoleEnum.ORG_ADMIN, RoleEnum.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        org_id = current_user["organization_id"]
        faculty_collection = db["faculty"]

        result = faculty_collection.update_one(
            {
                "_id": ObjectId(faculty_id),
                "organization_id": org_id,
            },
            {"$set": {"is_active": False, "deleted_at": datetime.utcnow()}},
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Faculty not found",
            )

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "delete_faculty",
            "resource": "faculty",
            "resource_id": faculty_id,
            "organization_id": org_id,
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {"message": "Faculty deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete faculty error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete faculty",
        )
