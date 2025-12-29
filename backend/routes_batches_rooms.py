"""
Batch and Room management API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from datetime import datetime
from backend.database import db, serialize_doc, serialize_docs
from bson import ObjectId
from schemas import BatchCreate, BatchResponse, RoomCreate, RoomResponse, RoleEnum
from auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ============ BATCHES ============

@router.post("/batches", response_model=dict)
async def create_batch(
    batch_data: BatchCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Create a new batch"""
    try:
        if current_user["role"] not in [RoleEnum.ORG_ADMIN, RoleEnum.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create batches",
            )

        org_id = current_user["organization_id"]
        batches_collection = db["batches"]

        # Check if batch exists
        if batches_collection.find_one({
            "organization_id": org_id,
            "name": batch_data.name,
        }):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch already exists",
            )

        batch_record = {
            "organization_id": org_id,
            "name": batch_data.name,
            "semester": batch_data.semester,
            "year": batch_data.year,
            "created_by": current_user["user_id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
        }

        result = batches_collection.insert_one(batch_record)
        batch_id = str(result.inserted_id)

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "create_batch",
            "resource": "batch",
            "resource_id": batch_id,
            "organization_id": org_id,
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {"message": "Batch created successfully", "batch_id": batch_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create batch error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/batches")
async def list_batches(
    current_user: dict = Depends(get_current_user),
):
    """List all batches in organization"""
    try:
        org_id = current_user["organization_id"]
        batches_collection = db["batches"]

        batches = list(batches_collection.find({
            "organization_id": org_id,
            "is_active": True,
        }))

        return {"total": len(batches), "batches": serialize_docs(batches)}

    except Exception as e:
        logger.error(f"List batches error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============ ROOMS ============

@router.post("/rooms", response_model=dict)
async def create_room(
    room_data: RoomCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Create a new room"""
    try:
        if current_user["role"] not in [RoleEnum.ORG_ADMIN, RoleEnum.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create rooms",
            )

        org_id = current_user["organization_id"]
        rooms_collection = db["rooms"]

        # Check if room code exists
        if rooms_collection.find_one({
            "organization_id": org_id,
            "code": room_data.code,
        }):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Room code already exists",
            )

        room_record = {
            "organization_id": org_id,
            "code": room_data.code,
            "capacity": room_data.capacity,
            "building": room_data.building,
            "floor": room_data.floor,
            "created_by": current_user["user_id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
        }

        result = rooms_collection.insert_one(room_record)
        room_id = str(result.inserted_id)

        # Log action
        audit_logs = db["audit_logs"]
        audit_logs.insert_one({
            "user_id": current_user["user_id"],
            "action": "create_room",
            "resource": "room",
            "resource_id": room_id,
            "organization_id": org_id,
            "ip_address": request.client.host if request.client else None,
            "created_at": datetime.utcnow(),
        })

        return {"message": "Room created successfully", "room_id": room_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create room error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/rooms")
async def list_rooms(
    building: str = None,
    current_user: dict = Depends(get_current_user),
):
    """List all rooms in organization"""
    try:
        org_id = current_user["organization_id"]
        rooms_collection = db["rooms"]

        filter_dict = {"organization_id": org_id, "is_active": True}
        if building:
            filter_dict["building"] = building

        rooms = list(rooms_collection.find(filter_dict))
        return {"total": len(rooms), "rooms": serialize_docs(rooms)}

    except Exception as e:
        logger.error(f"List rooms error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
