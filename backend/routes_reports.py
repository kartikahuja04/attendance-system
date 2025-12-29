"""
Reporting and export API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from datetime import datetime, timedelta
from backend.database import db, serialize_doc, serialize_docs
from bson import ObjectId
from schemas import ExportRequest, ExportResponse, RoleEnum
from auth import get_current_user
import logging
from io import BytesIO
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/attendance/student/{student_id}/summary")
async def get_student_attendance_summary(
    student_id: str,
    subject_id: str = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get attendance summary for a student"""
    try:
        org_id = current_user["organization_id"]
        
        # Students can only view their own attendance
        if current_user["role"] == RoleEnum.STUDENT:
            students_collection = db["students"]
            student = students_collection.find_one({
                "_id": ObjectId(student_id),
                "user_id": current_user["user_id"],
            })
            if not student:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied",
                )

        entries_collection = db["attendance_entries"]
        
        filter_dict = {
            "organization_id": org_id,
            "student_id": student_id,
        }
        
        if subject_id:
            filter_dict["subject_id"] = subject_id

        entries = list(entries_collection.find(filter_dict))

        # Calculate statistics
        total = len(entries)
        present = len([e for e in entries if e.get("status") == "present"])
        absent = len([e for e in entries if e.get("status") == "absent"])
        leave = len([e for e in entries if e.get("status") == "leave"])

        percentage = (present / total * 100) if total > 0 else 0

        return {
            "student_id": student_id,
            "total_classes": total,
            "present": present,
            "absent": absent,
            "leave": leave,
            "attendance_percentage": round(percentage, 2),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get student attendance summary error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/attendance/subject/{subject_id}/report")
async def get_subject_attendance_report(
    subject_id: str,
    batch_id: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get attendance report for a subject"""
    try:
        org_id = current_user["organization_id"]
        
        # Only admin and faculty can view reports
        if current_user["role"] not in [RoleEnum.ORG_ADMIN, RoleEnum.FACULTY, RoleEnum.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        sessions_collection = db["attendance_sessions"]
        entries_collection = db["attendance_entries"]
        students_collection = db["students"]

        filter_dict = {
            "organization_id": org_id,
            "subject_id": subject_id,
            "status": {"$ne": "cancelled"},
        }

        if batch_id:
            filter_dict["batch_id"] = batch_id
        
        if date_from:
            filter_dict["date"] = {"$gte": date_from}
        if date_to:
            if "date" in filter_dict:
                filter_dict["date"]["$lte"] = date_to
            else:
                filter_dict["date"] = {"$lte": date_to}

        sessions = list(sessions_collection.find(filter_dict))
        
        # Build report
        report_data = []
        for session in sessions:
            session_entries = list(entries_collection.find({
                "session_id": str(session["_id"]),
            }))

            for entry in session_entries:
                student = students_collection.find_one({
                    "_id": ObjectId(entry["student_id"]),
                })

                report_data.append({
                    "session_id": str(session["_id"]),
                    "date": session["date"],
                    "student_id": entry["student_id"],
                    "student_name": student.get("full_name") if student else "Unknown",
                    "roll_number": student.get("roll_number") if student else "",
                    "status": entry.get("status", "absent"),
                })

        return {
            "subject_id": subject_id,
            "total_entries": len(report_data),
            "data": report_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get subject attendance report error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/exports", response_model=dict)
async def create_export(
    export_req: ExportRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Create an export task"""
    try:
        org_id = current_user["organization_id"]
        exports_collection = db["exports"]

        export_record = {
            "organization_id": org_id,
            "type": export_req.type,
            "format": export_req.format,
            "filters": export_req.filters or {},
            "status": "pending",  # pending, completed, failed
            "created_by": current_user["user_id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "completed_at": None,
            "file_url": None,
        }

        result = exports_collection.insert_one(export_record)
        export_id = str(result.inserted_id)

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "create_export",
            "resource": "export",
            "resource_id": export_id,
            "organization_id": org_id,
            "changes": {"type": export_req.type, "format": export_req.format},
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {
            "message": "Export initiated",
            "export_id": export_id,
            "status": "pending",
        }

    except Exception as e:
        logger.error(f"Create export error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/exports/{export_id}")
async def get_export_status(
    export_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get export status and download link"""
    try:
        org_id = current_user["organization_id"]
        exports_collection = db["exports"]

        export = exports_collection.find_one({
            "_id": ObjectId(export_id),
            "organization_id": org_id,
        })

        if not export:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export not found",
            )

        return {
            "export_id": str(export["_id"]),
            "status": export["status"],
            "type": export["type"],
            "format": export["format"],
            "file_url": export.get("file_url"),
            "created_at": export["created_at"],
            "completed_at": export.get("completed_at"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get export status error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
