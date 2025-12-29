"""
Notifications and Audit Logs API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from datetime import datetime
from backend.database import db, serialize_doc, serialize_docs
from bson import ObjectId
from schemas import NotificationResponse, AuditLogResponse, RoleEnum
from auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ============ NOTIFICATIONS ============

@router.get("/notifications", response_model=dict)
async def get_notifications(
    skip: int = Query(0),
    limit: int = Query(20),
    unread_only: bool = Query(False),
    current_user: dict = Depends(get_current_user),
):
    """Get user notifications"""
    try:
        notifications_collection = db["notifications"]

        filter_dict = {
            "organization_id": current_user["organization_id"],
            "user_id": current_user["user_id"],
        }

        if unread_only:
            filter_dict["read_at"] = None

        total = notifications_collection.count_documents(filter_dict)
        notifications = list(
            notifications_collection.find(filter_dict)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "notifications": serialize_docs(notifications),
        }

    except Exception as e:
        logger.error(f"Get notifications error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark notification as read"""
    try:
        notifications_collection = db["notifications"]

        result = notifications_collection.update_one(
            {
                "_id": ObjectId(notification_id),
                "user_id": current_user["user_id"],
            },
            {"$set": {"read_at": datetime.utcnow()}},
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        return {"message": "Notification marked as read"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mark notification read error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    current_user: dict = Depends(get_current_user),
):
    """Mark all notifications as read"""
    try:
        notifications_collection = db["notifications"]

        result = notifications_collection.update_many(
            {
                "organization_id": current_user["organization_id"],
                "user_id": current_user["user_id"],
                "read_at": None,
            },
            {"$set": {"read_at": datetime.utcnow()}},
        )

        return {
            "message": "All notifications marked as read",
            "count": result.modified_count,
        }

    except Exception as e:
        logger.error(f"Mark all notifications read error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def create_notification(user_id, title, message, notification_type, org_id):
    """Helper function to create a notification"""
    try:
        notifications_collection = db["notifications"]
        notification = {
            "organization_id": org_id,
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": notification_type,  # alert, info, warning
            "created_at": datetime.utcnow(),
            "read_at": None,
        }
        result = notifications_collection.insert_one(notification)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        return None


# ============ AUDIT LOGS ============

@router.get("/audit-logs", response_model=dict)
async def get_audit_logs(
    action: str = Query(None),
    resource: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    current_user: dict = Depends(get_current_user),
):
    """Get audit logs (Admin only)"""
    try:
        # Only admins can view audit logs
        if current_user["role"] not in [RoleEnum.ORG_ADMIN, RoleEnum.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        audit_logs_collection = db["audit_logs"]

        filter_dict = {
            "organization_id": current_user["organization_id"],
        }

        if action:
            filter_dict["action"] = action
        if resource:
            filter_dict["resource"] = resource

        total = audit_logs_collection.count_documents(filter_dict)
        logs = list(
            audit_logs_collection.find(filter_dict)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "logs": serialize_docs(logs),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get audit logs error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/audit-logs/user/{user_id}")
async def get_user_audit_logs(
    user_id: str,
    skip: int = Query(0),
    limit: int = Query(50),
    current_user: dict = Depends(get_current_user),
):
    """Get audit logs for a specific user"""
    try:
        # Only admins can view audit logs
        if current_user["role"] not in [RoleEnum.ORG_ADMIN, RoleEnum.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        audit_logs_collection = db["audit_logs"]

        filter_dict = {
            "organization_id": current_user["organization_id"],
            "user_id": user_id,
        }

        total = audit_logs_collection.count_documents(filter_dict)
        logs = list(
            audit_logs_collection.find(filter_dict)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "logs": serialize_docs(logs),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user audit logs error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def log_audit_action(user_id, action, resource, resource_id, org_id, changes=None, ip_address=None):
    """Helper function to log an audit action"""
    try:
        audit_logs_collection = db["audit_logs"]
        log_entry = {
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "organization_id": org_id,
            "changes": changes,
            "ip_address": ip_address,
            "created_at": datetime.utcnow(),
        }
        audit_logs_collection.insert_one(log_entry)
    except Exception as e:
        logger.error(f"Error logging audit action: {e}")
