"""
Attendance management API endpoints (CRITICAL MODULE)
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from datetime import datetime, timedelta
from backend.database import db, serialize_doc, serialize_docs
from bson import ObjectId
from schemas import (
    AttendanceSessionCreate,
    AttendanceSessionResponse,
    AttendanceEntryCreate,
    AttendanceEntryResponse,
    RoleEnum,
)
from auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sessions", response_model=dict)
async def create_attendance_session(
    session_data: AttendanceSessionCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Create a new attendance session (Faculty only)"""
    try:
        # Only faculty can create sessions
        if current_user["role"] != RoleEnum.FACULTY:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only faculty can create attendance sessions",
            )

        org_id = current_user["organization_id"]
        sessions_collection = db["attendance_sessions"]
        faculty_collection = db["faculty"]
        subject_collection = db["subjects"]
        batch_collection = db["batches"]
        students_collection = db["students"]

        # Verify faculty owns the request
        faculty = faculty_collection.find_one({
            "_id": ObjectId(session_data.faculty_id),
            "organization_id": org_id,
        })

        if not faculty or str(faculty["user_id"]) != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only create sessions for yourself",
            )

        # Verify subject exists
        subject = subject_collection.find_one({
            "_id": ObjectId(session_data.subject_id),
            "organization_id": org_id,
        })
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject not found",
            )

        # Verify batch exists
        batch = batch_collection.find_one({
            "_id": ObjectId(session_data.batch_id),
            "organization_id": org_id,
        })
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch not found",
            )

        # Check for duplicate session (same faculty, subject, batch, date, time)
        existing = sessions_collection.find_one({
            "organization_id": org_id,
            "faculty_id": session_data.faculty_id,
            "subject_id": session_data.subject_id,
            "batch_id": session_data.batch_id,
            "date": session_data.date,
            "start_time": session_data.start_time,
            "status": {"$ne": "cancelled"},
        })

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attendance session already exists for this slot",
            )

        # Get students in batch
        students = list(students_collection.find({
            "organization_id": org_id,
            "batch": batch["name"],
            "is_active": True,
        }))

        # Create session
        session_record = {
            "organization_id": org_id,
            "faculty_id": session_data.faculty_id,
            "subject_id": session_data.subject_id,
            "batch_id": session_data.batch_id,
            "room_id": session_data.room_id,
            "date": session_data.date,
            "start_time": session_data.start_time,
            "end_time": session_data.end_time,
            "status": "active",  # active, locked, cancelled
            "student_count": len(students),
            "present_count": 0,
            "absent_count": 0,
            "leave_count": 0,
            "created_by": current_user["user_id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "locked_at": None,
            "locked_by": None,
        }

        session_result = sessions_collection.insert_one(session_record)
        session_id = str(session_result.inserted_id)

        # Create attendance entries (all absent by default)
        entries_collection = db["attendance_entries"]
        entries_to_insert = []

        for student in students:
            entries_to_insert.append({
                "organization_id": org_id,
                "session_id": session_id,
                "student_id": str(student["_id"]),
                "user_id": student["user_id"],
                "status": "absent",  # present, absent, leave
                "marked_at": None,
                "marked_by": None,
                "edited_at": None,
                "edited_by": None,
            })

        if entries_to_insert:
            entries_collection.insert_many(entries_to_insert)

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "create_attendance_session",
            "resource": "attendance_session",
            "resource_id": session_id,
            "organization_id": org_id,
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {
            "message": "Attendance session created successfully",
            "session_id": session_id,
            "student_count": len(students),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create attendance session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create attendance session",
        )


@router.get("/sessions/{session_id}", response_model=dict)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get attendance session with entries"""
    try:
        org_id = current_user["organization_id"]
        sessions_collection = db["attendance_sessions"]
        entries_collection = db["attendance_entries"]
        students_collection = db["students"]

        session = sessions_collection.find_one({
            "_id": ObjectId(session_id),
            "organization_id": org_id,
        })

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Check permissions
        if current_user["role"] == RoleEnum.FACULTY:
            faculty_collection = db["faculty"]
            faculty = faculty_collection.find_one({"_id": ObjectId(session["faculty_id"])})
            if str(faculty["user_id"]) != current_user["user_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only view your own sessions",
                )
        elif current_user["role"] == RoleEnum.STUDENT:
            # Students can only view if in the batch
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students cannot view individual sessions",
            )

        # Get attendance entries
        entries = list(entries_collection.find({"session_id": session_id}))

        # Enrich entries with student info
        for entry in entries:
            student = students_collection.find_one({"_id": ObjectId(entry["student_id"])})
            if student:
                entry["student_name"] = student.get("full_name", "Unknown")
                entry["roll_number"] = student.get("roll_number", "")

        return {
            "session": serialize_doc(session),
            "entries": serialize_docs(entries),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch session",
        )


@router.post("/sessions/{session_id}/mark", response_model=dict)
async def mark_attendance(
    session_id: str,
    markings: dict,  # {"student_id": "present"/"absent"/"leave"}
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Mark attendance for students in a session"""
    try:
        if current_user["role"] != RoleEnum.FACULTY:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only faculty can mark attendance",
            )

        org_id = current_user["organization_id"]
        sessions_collection = db["attendance_sessions"]
        entries_collection = db["attendance_entries"]
        faculty_collection = db["faculty"]

        session = sessions_collection.find_one({
            "_id": ObjectId(session_id),
            "organization_id": org_id,
        })

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Verify faculty
        faculty = faculty_collection.find_one({"_id": ObjectId(session["faculty_id"])})
        if str(faculty["user_id"]) != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only mark attendance for your own sessions",
            )

        # Check if session is locked
        if session["status"] == "locked":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot mark attendance in a locked session",
            )

        # Update entries
        present_count = 0
        absent_count = 0
        leave_count = 0

        for student_id, status in markings.items():
            if status not in ["present", "absent", "leave"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}",
                )

            result = entries_collection.update_one(
                {
                    "session_id": session_id,
                    "student_id": student_id,
                },
                {
                    "$set": {
                        "status": status,
                        "marked_at": datetime.utcnow(),
                        "marked_by": current_user["user_id"],
                    }
                },
            )

            if result.matched_count == 0:
                logger.warning(f"Entry not found for student {student_id} in session {session_id}")
                continue

            # Count statuses
            if status == "present":
                present_count += 1
            elif status == "absent":
                absent_count += 1
            elif status == "leave":
                leave_count += 1

        # Update session counts
        sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "present_count": present_count,
                    "absent_count": absent_count,
                    "leave_count": leave_count,
                    "updated_at": datetime.utcnow(),
                    "last_marked_by": current_user["user_id"],
                }
            },
        )

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "mark_attendance",
            "resource": "attendance_session",
            "resource_id": session_id,
            "organization_id": org_id,
            "changes": {
                "present": present_count,
                "absent": absent_count,
                "leave": leave_count,
            },
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {
            "message": "Attendance marked successfully",
            "present_count": present_count,
            "absent_count": absent_count,
            "leave_count": leave_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mark attendance error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark attendance",
        )


@router.post("/sessions/{session_id}/lock")
async def lock_attendance_session(
    session_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Lock an attendance session (immutable)"""
    try:
        org_id = current_user["organization_id"]
        sessions_collection = db["attendance_sessions"]
        faculty_collection = db["faculty"]

        session = sessions_collection.find_one({
            "_id": ObjectId(session_id),
            "organization_id": org_id,
        })

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Faculty can lock their own sessions
        # Admin can lock any session in the org
        if current_user["role"] == RoleEnum.FACULTY:
            faculty = faculty_collection.find_one({"_id": ObjectId(session["faculty_id"])})
            if str(faculty["user_id"]) != current_user["user_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only lock your own sessions",
                )

        # Lock the session
        sessions_collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "status": "locked",
                    "locked_at": datetime.utcnow(),
                    "locked_by": current_user["user_id"],
                }
            },
        )

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "lock_attendance_session",
            "resource": "attendance_session",
            "resource_id": session_id,
            "organization_id": org_id,
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {"message": "Attendance session locked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lock session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to lock session",
        )
