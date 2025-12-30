"""
Role-Based Access Control (RBAC) and permission system
"""
from enum import Enum
from typing import List, Dict, Callable
from fastapi import HTTPException, status, Depends


class RoleEnum(str, Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    FACULTY = "faculty"
    STUDENT = "student"


class PermissionEnum(str, Enum):
    # Organization Management
    CREATE_ORGANIZATION = "create_organization"
    MANAGE_ORGANIZATION = "manage_organization"
    VIEW_ORGANIZATION = "view_organization"
    DELETE_ORGANIZATION = "delete_organization"

    # User Management
    CREATE_USER = "create_user"
    EDIT_USER = "edit_user"
    DELETE_USER = "delete_user"
    VIEW_USERS = "view_users"

    # Student Management
    CREATE_STUDENT = "create_student"
    EDIT_STUDENT = "edit_student"
    DELETE_STUDENT = "delete_student"
    VIEW_STUDENTS = "view_students"
    BULK_IMPORT_STUDENTS = "bulk_import_students"

    # Faculty Management
    CREATE_FACULTY = "create_faculty"
    EDIT_FACULTY = "edit_faculty"
    DELETE_FACULTY = "delete_faculty"
    VIEW_FACULTY = "view_faculty"

    # Subject Management
    CREATE_SUBJECT = "create_subject"
    EDIT_SUBJECT = "edit_subject"
    DELETE_SUBJECT = "delete_subject"
    VIEW_SUBJECTS = "view_subjects"

    # Timetable Management
    CREATE_TIMETABLE = "create_timetable"
    EDIT_TIMETABLE = "edit_timetable"
    DELETE_TIMETABLE = "delete_timetable"
    VIEW_TIMETABLE = "view_timetable"

    # Attendance Management
    MARK_ATTENDANCE = "mark_attendance"
    EDIT_ATTENDANCE = "edit_attendance"
    LOCK_ATTENDANCE = "lock_attendance"
    VIEW_ATTENDANCE = "view_attendance"
    EXPORT_ATTENDANCE = "export_attendance"

    # Reports
    VIEW_REPORTS = "view_reports"
    CREATE_REPORTS = "create_reports"
    EXPORT_REPORTS = "export_reports"

    # Admin Functions
    VIEW_AUDIT_LOGS = "view_audit_logs"
    OVERRIDE_ATTENDANCE = "override_attendance"
    MANAGE_RULES = "manage_rules"
    MANAGE_NOTIFICATIONS = "manage_notifications"


# Permission Matrix: Role -> List of Permissions
PERMISSION_MATRIX: Dict[RoleEnum, List[PermissionEnum]] = {
    RoleEnum.SUPER_ADMIN: [
        # Full access to all permissions
        PermissionEnum.CREATE_ORGANIZATION,
        PermissionEnum.MANAGE_ORGANIZATION,
        PermissionEnum.VIEW_ORGANIZATION,
        PermissionEnum.DELETE_ORGANIZATION,
        PermissionEnum.CREATE_USER,
        PermissionEnum.EDIT_USER,
        PermissionEnum.DELETE_USER,
        PermissionEnum.VIEW_USERS,
        PermissionEnum.CREATE_STUDENT,
        PermissionEnum.EDIT_STUDENT,
        PermissionEnum.DELETE_STUDENT,
        PermissionEnum.VIEW_STUDENTS,
        PermissionEnum.BULK_IMPORT_STUDENTS,
        PermissionEnum.CREATE_FACULTY,
        PermissionEnum.EDIT_FACULTY,
        PermissionEnum.DELETE_FACULTY,
        PermissionEnum.VIEW_FACULTY,
        PermissionEnum.CREATE_SUBJECT,
        PermissionEnum.EDIT_SUBJECT,
        PermissionEnum.DELETE_SUBJECT,
        PermissionEnum.VIEW_SUBJECTS,
        PermissionEnum.CREATE_TIMETABLE,
        PermissionEnum.EDIT_TIMETABLE,
        PermissionEnum.DELETE_TIMETABLE,
        PermissionEnum.VIEW_TIMETABLE,
        PermissionEnum.MARK_ATTENDANCE,
        PermissionEnum.EDIT_ATTENDANCE,
        PermissionEnum.LOCK_ATTENDANCE,
        PermissionEnum.VIEW_ATTENDANCE,
        PermissionEnum.EXPORT_ATTENDANCE,
        PermissionEnum.VIEW_REPORTS,
        PermissionEnum.CREATE_REPORTS,
        PermissionEnum.EXPORT_REPORTS,
        PermissionEnum.VIEW_AUDIT_LOGS,
        PermissionEnum.OVERRIDE_ATTENDANCE,
        PermissionEnum.MANAGE_RULES,
        PermissionEnum.MANAGE_NOTIFICATIONS,
    ],
    RoleEnum.ORG_ADMIN: [
        PermissionEnum.VIEW_ORGANIZATION,
        PermissionEnum.MANAGE_ORGANIZATION,
        PermissionEnum.CREATE_USER,
        PermissionEnum.EDIT_USER,
        PermissionEnum.VIEW_USERS,
        PermissionEnum.CREATE_STUDENT,
        PermissionEnum.EDIT_STUDENT,
        PermissionEnum.VIEW_STUDENTS,
        PermissionEnum.BULK_IMPORT_STUDENTS,
        PermissionEnum.CREATE_FACULTY,
        PermissionEnum.EDIT_FACULTY,
        PermissionEnum.VIEW_FACULTY,
        PermissionEnum.CREATE_SUBJECT,
        PermissionEnum.EDIT_SUBJECT,
        PermissionEnum.VIEW_SUBJECTS,
        PermissionEnum.CREATE_TIMETABLE,
        PermissionEnum.EDIT_TIMETABLE,
        PermissionEnum.VIEW_TIMETABLE,
        PermissionEnum.VIEW_ATTENDANCE,
        PermissionEnum.LOCK_ATTENDANCE,
        PermissionEnum.EDIT_ATTENDANCE,  # Limited: only unlock/override
        PermissionEnum.EXPORT_ATTENDANCE,
        PermissionEnum.VIEW_REPORTS,
        PermissionEnum.CREATE_REPORTS,
        PermissionEnum.EXPORT_REPORTS,
        PermissionEnum.VIEW_AUDIT_LOGS,
        PermissionEnum.OVERRIDE_ATTENDANCE,
        PermissionEnum.MANAGE_RULES,
        PermissionEnum.MANAGE_NOTIFICATIONS,
    ],
    RoleEnum.FACULTY: [
        PermissionEnum.VIEW_ORGANIZATION,
        PermissionEnum.VIEW_STUDENTS,
        PermissionEnum.VIEW_SUBJECTS,
        PermissionEnum.VIEW_TIMETABLE,
        PermissionEnum.MARK_ATTENDANCE,
        PermissionEnum.EDIT_ATTENDANCE,  # Limited: only own sessions, within time window
        PermissionEnum.VIEW_ATTENDANCE,  # Limited: own sessions
        PermissionEnum.EXPORT_ATTENDANCE,  # Limited: own sessions
        PermissionEnum.VIEW_REPORTS,  # Limited: own subjects
        PermissionEnum.CREATE_REPORTS,  # Limited: own subjects
        PermissionEnum.EXPORT_REPORTS,  # Limited: own subjects
    ],
    RoleEnum.STUDENT: [
        PermissionEnum.VIEW_TIMETABLE,
        PermissionEnum.VIEW_ATTENDANCE,  # Limited: own attendance only
        PermissionEnum.VIEW_REPORTS,  # Limited: own attendance
    ],
}


def has_permission(
    user: dict, permission: PermissionEnum, organization_id: str = None
) -> bool:
    """Check if a user has a specific permission"""
    role = RoleEnum(user.get("role"))
    permissions = PERMISSION_MATRIX.get(role, [])

    has_perm = permission in permissions

    # Check organization isolation
    if organization_id and user.get("organization_id") != organization_id:
        return False

    return has_perm


def require_permission(permission: PermissionEnum):
    """Dependency for permission-based access control"""
    async def dep(user: dict = Depends(get_current_user)):
        if not has_permission(user, permission, user.get("organization_id")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}",
            )
        return user

    return dep


def require_role(*roles: RoleEnum):
    """Dependency factory for role-based access control"""
    async def dep(user: dict = Depends(get_current_user)):
        if RoleEnum(user.get("role")) not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role for this action",
            )
        return user

    return dep


# Import get_current_user from auth module
try:
    from auth import get_current_user
except ImportError:
    from .auth import get_current_user
