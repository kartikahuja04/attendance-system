"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RoleEnum(str, Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    FACULTY = "faculty"
    STUDENT = "student"


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: RoleEnum


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
    organization_id: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    user: UserResponse


class OrganizationCreate(BaseModel):
    name: str
    code: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None


class OrganizationResponse(OrganizationCreate):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class StudentCreate(BaseModel):
    email: EmailStr
    full_name: str
    roll_number: str
    batch: str
    semester: int


class StudentResponse(StudentCreate):
    id: str
    organization_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class FacultyCreate(BaseModel):
    email: EmailStr
    full_name: str
    employee_id: str
    department: str


class FacultyResponse(FacultyCreate):
    id: str
    organization_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class SubjectCreate(BaseModel):
    code: str
    name: str
    department: str
    semester: int


class SubjectResponse(SubjectCreate):
    id: str
    organization_id: str

    class Config:
        from_attributes = True


class BatchCreate(BaseModel):
    name: str
    semester: int
    year: int


class BatchResponse(BatchCreate):
    id: str
    organization_id: str

    class Config:
        from_attributes = True


class RoomCreate(BaseModel):
    code: str
    capacity: int
    building: str
    floor: int


class RoomResponse(RoomCreate):
    id: str
    organization_id: str

    class Config:
        from_attributes = True


class TimeSlotCreate(BaseModel):
    day: str  # Monday, Tuesday, etc.
    start_time: str  # HH:MM format
    end_time: str  # HH:MM format


class TimetableCreate(BaseModel):
    faculty_id: str
    subject_id: str
    batch_id: str
    room_id: str
    time_slots: List[TimeSlotCreate]


class TimetableResponse(TimetableCreate):
    id: str
    organization_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceSessionCreate(BaseModel):
    subject_id: str
    batch_id: str
    faculty_id: str
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM:SS
    end_time: Optional[str] = None
    room_id: Optional[str] = None


class AttendanceSessionResponse(AttendanceSessionCreate):
    id: str
    organization_id: str
    status: str  # active, locked, cancelled
    student_count: int
    present_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceEntryCreate(BaseModel):
    session_id: str
    student_id: str
    status: str  # present, absent, leave
    marked_by: Optional[str] = "manual"  # manual, qr, nfc


class AttendanceEntryResponse(AttendanceEntryCreate):
    id: str
    marked_at: datetime
    edited_at: Optional[datetime] = None
    edited_by: Optional[str] = None

    class Config:
        from_attributes = True


class AttendanceRuleCreate(BaseModel):
    name: str
    min_attendance_percentage: float
    allow_backdated_marking: bool
    max_backdated_days: int
    allow_faculty_edit: bool
    allow_admin_override: bool


class AttendanceRuleResponse(AttendanceRuleCreate):
    id: str
    organization_id: str

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    user_id: str
    title: str
    message: str
    type: str  # alert, info, warning


class NotificationResponse(NotificationCreate):
    id: str
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditLogCreate(BaseModel):
    user_id: str
    action: str
    resource: str
    resource_id: str
    changes: Optional[dict] = None
    ip_address: Optional[str] = None


class AuditLogResponse(AuditLogCreate):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ExportRequest(BaseModel):
    type: str  # daily, subject_wise, student_wise
    format: str  # excel, pdf
    filters: Optional[dict] = None


class ExportResponse(BaseModel):
    id: str
    status: str  # pending, completed, failed
    file_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    user_id: str
    email: str
    role: RoleEnum
    organization_id: str
