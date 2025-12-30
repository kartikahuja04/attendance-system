"""
Student management API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from datetime import datetime
from backend.database import db, serialize_doc, serialize_docs
from bson import ObjectId
from schemas import StudentCreate, StudentResponse, RoleEnum
from auth import get_current_user, hash_password
from permissions import require_permission, PermissionEnum
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/students", response_model=dict)
async def create_student(
    student_data: StudentCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Create a new student (Admin only)"""
    try:
        # Check permission
        if not any(role == current_user["role"] for role in [RoleEnum.ORG_ADMIN, RoleEnum.SUPER_ADMIN]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create students",
            )

        org_id = current_user["organization_id"]
        students_collection = db["students"]
        users_collection = db["users"]

        # Check if student with same roll number exists in org
        if students_collection.find_one({
            "organization_id": org_id,
            "roll_number": student_data.roll_number,
        }):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Roll number already exists in this organization",
            )

        # Check if email exists
        if users_collection.find_one({"email": student_data.email}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create user account for student
        user_data = {
            "email": student_data.email,
            "full_name": student_data.full_name,
            "password_hash": hash_password("default123"),  # Temporary password
            "role": RoleEnum.STUDENT,
            "organization_id": org_id,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        user_result = users_collection.insert_one(user_data)
        user_id = str(user_result.inserted_id)

        # Create student record
        student_record = {
            "user_id": user_id,
            "organization_id": org_id,
            "email": student_data.email,
            "full_name": student_data.full_name,
            "roll_number": student_data.roll_number,
            "batch": student_data.batch,
            "semester": student_data.semester,
            "created_by": current_user["user_id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
        }

        student_result = students_collection.insert_one(student_record)
        student_id = str(student_result.inserted_id)

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "create_student",
            "resource": "student",
            "resource_id": student_id,
            "organization_id": org_id,
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {
            "message": "Student created successfully",
            "student_id": student_id,
            "user_id": user_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create student error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create student",
        )


@router.get("/students", response_model=dict)
async def list_students(
    batch: str = Query(None),
    semester: int = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    current_user: dict = Depends(get_current_user),
):
    """List students in organization"""
    try:
        # Only admins and faculty can view students
        if current_user["role"] not in [RoleEnum.ORG_ADMIN, RoleEnum.FACULTY, RoleEnum.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        org_id = current_user["organization_id"]
        students_collection = db["students"]

        # Build filter
        filter_dict = {"organization_id": org_id, "is_active": True}
        if batch:
            filter_dict["batch"] = batch
        if semester is not None:
            filter_dict["semester"] = semester

        # Get total count
        total = students_collection.count_documents(filter_dict)

        # Get paginated results
        students = list(students_collection.find(filter_dict).skip(skip).limit(limit))

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "students": serialize_docs(students),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List students error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch students",
        )


@router.get("/students/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get student details"""
    try:
        org_id = current_user["organization_id"]
        students_collection = db["students"]

        student = students_collection.find_one({
            "_id": ObjectId(student_id),
            "organization_id": org_id,
        })

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        return StudentResponse(
            id=str(student["_id"]),
            email=student["email"],
            full_name=student["full_name"],
            roll_number=student["roll_number"],
            batch=student["batch"],
            semester=student["semester"],
            organization_id=org_id,
            created_at=student["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get student error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch student",
        )


@router.put("/students/{student_id}")
async def update_student(
    student_id: str,
    student_data: StudentCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Update student details"""
    try:
        # Only admins can edit students
        if current_user["role"] not in [RoleEnum.ORG_ADMIN, RoleEnum.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        org_id = current_user["organization_id"]
        students_collection = db["students"]
        users_collection = db["users"]

        student = students_collection.find_one({
            "_id": ObjectId(student_id),
            "organization_id": org_id,
        })

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        # Update student record
        update_data = {
            "full_name": student_data.full_name,
            "batch": student_data.batch,
            "semester": student_data.semester,
            "updated_at": datetime.utcnow(),
        }

        students_collection.update_one(
            {"_id": ObjectId(student_id)},
            {"$set": update_data},
        )

        # Update user record
        users_collection.update_one(
            {"_id": ObjectId(student["user_id"])},
            {"$set": {"full_name": student_data.full_name, "updated_at": datetime.utcnow()}},
        )

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "update_student",
            "resource": "student",
            "resource_id": student_id,
            "organization_id": org_id,
            "changes": update_data,
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {"message": "Student updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update student error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update student",
        )


@router.delete("/students/{student_id}")
async def delete_student(
    student_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Soft delete a student"""
    try:
        # Only admins can delete students
        if current_user["role"] not in [RoleEnum.ORG_ADMIN, RoleEnum.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        org_id = current_user["organization_id"]
        students_collection = db["students"]

        result = students_collection.update_one(
            {
                "_id": ObjectId(student_id),
                "organization_id": org_id,
            },
            {"$set": {"is_active": False, "deleted_at": datetime.utcnow()}},
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "delete_student",
            "resource": "student",
            "resource_id": student_id,
            "organization_id": org_id,
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {"message": "Student deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete student error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete student",
        )
