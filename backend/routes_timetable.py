"""
Subject and timetable management API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from datetime import datetime
from backend.database import db, serialize_doc, serialize_docs
from bson import ObjectId
from schemas import SubjectCreate, SubjectResponse, TimetableCreate, TimetableResponse, RoleEnum
from auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ============ SUBJECTS ============

@router.post("/subjects", response_model=dict)
async def create_subject(
    subject_data: SubjectCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Create a new subject"""
    try:
        if current_user["role"] not in [RoleEnum.ORG_ADMIN, RoleEnum.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create subjects",
            )

        org_id = current_user["organization_id"]
        subjects_collection = db["subjects"]

        # Check if subject code exists
        if subjects_collection.find_one({
            "organization_id": org_id,
            "code": subject_data.code,
        }):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject code already exists",
            )

        subject_record = {
            "organization_id": org_id,
            "code": subject_data.code,
            "name": subject_data.name,
            "department": subject_data.department,
            "semester": subject_data.semester,
            "created_by": current_user["user_id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
        }

        result = subjects_collection.insert_one(subject_record)
        subject_id = str(result.inserted_id)

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "create_subject",
            "resource": "subject",
            "resource_id": subject_id,
            "organization_id": org_id,
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {"message": "Subject created successfully", "subject_id": subject_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create subject error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/subjects")
async def list_subjects(
    department: str = Query(None),
    semester: int = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """List subjects in organization"""
    try:
        org_id = current_user["organization_id"]
        subjects_collection = db["subjects"]

        filter_dict = {"organization_id": org_id, "is_active": True}
        if department:
            filter_dict["department"] = department
        if semester is not None:
            filter_dict["semester"] = semester

        subjects = list(subjects_collection.find(filter_dict))
        return {"total": len(subjects), "subjects": serialize_docs(subjects)}

    except Exception as e:
        logger.error(f"List subjects error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============ TIMETABLES ============

@router.post("/timetables", response_model=dict)
async def create_timetable(
    timetable_data: TimetableCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Create a new timetable entry"""
    try:
        if current_user["role"] not in [RoleEnum.ORG_ADMIN, RoleEnum.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create timetables",
            )

        org_id = current_user["organization_id"]
        timetables_collection = db["timetables"]
        faculty_collection = db["faculty"]

        # Verify faculty exists
        faculty = faculty_collection.find_one({
            "_id": ObjectId(timetable_data.faculty_id),
            "organization_id": org_id,
        })
        if not faculty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Faculty not found",
            )

        # Check for room conflicts
        for slot in timetable_data.time_slots:
            conflict = timetables_collection.find_one({
                "organization_id": org_id,
                "room_id": timetable_data.room_id,
                "time_slots": {
                    "$elemMatch": {
                        "day": slot.day,
                        "start_time": {"$lt": slot.end_time},
                        "end_time": {"$gt": slot.start_time},
                    }
                },
                "is_active": True,
            })
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Room conflict on {slot.day}",
                )

        # Check for faculty conflicts
        for slot in timetable_data.time_slots:
            conflict = timetables_collection.find_one({
                "organization_id": org_id,
                "faculty_id": timetable_data.faculty_id,
                "time_slots": {
                    "$elemMatch": {
                        "day": slot.day,
                        "start_time": {"$lt": slot.end_time},
                        "end_time": {"$gt": slot.start_time},
                    }
                },
                "is_active": True,
            })
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Faculty already has a class on {slot.day}",
                )

        timetable_record = {
            "organization_id": org_id,
            "faculty_id": timetable_data.faculty_id,
            "subject_id": timetable_data.subject_id,
            "batch_id": timetable_data.batch_id,
            "room_id": timetable_data.room_id,
            "time_slots": [slot.dict() for slot in timetable_data.time_slots],
            "created_by": current_user["user_id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
        }

        result = timetables_collection.insert_one(timetable_record)
        timetable_id = str(result.inserted_id)

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "create_timetable",
            "resource": "timetable",
            "resource_id": timetable_id,
            "organization_id": org_id,
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {"message": "Timetable created successfully", "timetable_id": timetable_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create timetable error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/timetables/faculty/{faculty_id}")
async def get_faculty_timetable(
    faculty_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get timetable for a faculty"""
    try:
        org_id = current_user["organization_id"]
        timetables_collection = db["timetables"]

        timetables = list(timetables_collection.find({
            "organization_id": org_id,
            "faculty_id": faculty_id,
            "is_active": True,
        }))

        return {"total": len(timetables), "timetables": serialize_docs(timetables)}

    except Exception as e:
        logger.error(f"Get faculty timetable error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/timetables/batch/{batch_id}")
async def get_batch_timetable(
    batch_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get timetable for a batch"""
    try:
        org_id = current_user["organization_id"]
        timetables_collection = db["timetables"]

        timetables = list(timetables_collection.find({
            "organization_id": org_id,
            "batch_id": batch_id,
            "is_active": True,
        }))

        return {"total": len(timetables), "timetables": serialize_docs(timetables)}

    except Exception as e:
        logger.error(f"Get batch timetable error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
