# 🎓 University Attendance Management System v2.0

**Production-Ready | Enterprise-Grade | Scalable | Secure**

---

## 📋 Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Installation & Setup](#installation--setup)
- [Database Schema](#database-schema)
- [API Documentation](#api-documentation)
- [Features by Role](#features-by-role)
- [Security](#security)
- [Deployment](#deployment)

---

## Overview

A complete university attendance management system built with:
- **Backend**: FastAPI (Python)
- **Frontend**: React + Vite
- **Database**: MongoDB
- **Authentication**: JWT with Role-Based Access Control (RBAC)

### Key Features
✅ **Complete Permission System** - 4 roles with granular permissions
✅ **Attendance Immutability** - Locked sessions prevent tampering
✅ **Organization Isolation** - Multi-tenant support with strict data segregation
✅ **Audit Logging** - All critical actions logged
✅ **Real-time Statistics** - Attendance summaries and reports
✅ **Export Functionality** - Excel and PDF reports
✅ **No Hardcoded Data** - Everything API-driven
✅ **Production Hardened** - Error handling, rate limiting ready

---

## System Architecture

### Database Collections (MongoDB)

```
platform_admins          - System super admins
organizations           - Institutes/Universities
organization_settings   - Config per organization
users                  - All user accounts
students               - Student details & enrollment
faculty                - Faculty profiles
subjects               - Course information
courses                - Course assignments
batches                - Student batches/cohorts
rooms                  - Classroom/lab locations
timetables             - Class schedule
attendance_sessions    - Attendance records (immutable)
attendance_entries     - Individual student attendance
attendance_rules       - Org-specific attendance policies
notifications          - User notifications
audit_logs            - Complete action history
exports               - Generated reports
login_history         - Authentication logs
```

### Role-Based Access Control Matrix

| Permission | Super Admin | Org Admin | Faculty | Student |
|-----------|---|---|---|---|
| Create Organization | ✅ | ❌ | ❌ | ❌ |
| Manage Users | ✅ | ✅ | ❌ | ❌ |
| Create Students | ✅ | ✅ | ❌ | ❌ |
| Create Faculty | ✅ | ✅ | ❌ | ❌ |
| Mark Attendance | ❌ | ❌ | ✅ | ❌ |
| Edit Attendance | ⏱️* | ✅ | ⏱️* | ❌ |
| Lock Attendance | ❌ | ✅ | ✅ | ❌ |
| View Own Attendance | ✅ | ✅ | ✅ | ✅ |
| View Reports | ✅ | ✅ | ⏱️** | ⏱️** |
| Export Attendance | ✅ | ✅ | ⏱️** | ❌ |

*Limited: within time window, with admin approval
**Limited: own data only

---

## Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- MongoDB 4.0+
- pip, npm

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r ../requirements.txt

# Set environment variables
# Create .env file
MONGODB_URI=mongodb://localhost:27017
DB_NAME=attendance_system
SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256

# Run database initialization
python -c "from database import init_db; init_db()"

# Start server
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file
REACT_APP_API_URL=http://localhost:8000/api

# Start development server
npm run dev
```

---

## Database Schema

### Users Collection
```json
{
  "_id": "ObjectId",
  "email": "student@university.edu",
  "full_name": "John Doe",
  "password_hash": "bcrypt_hash",
  "role": "student",
  "organization_id": "ObjectId",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Attendance Sessions
```json
{
  "_id": "ObjectId",
  "organization_id": "ObjectId",
  "faculty_id": "ObjectId",
  "subject_id": "ObjectId",
  "batch_id": "ObjectId",
  "room_id": "ObjectId",
  "date": "2024-01-15",
  "start_time": "09:00:00",
  "end_time": "10:00:00",
  "status": "locked",
  "student_count": 45,
  "present_count": 42,
  "absent_count": 3,
  "leave_count": 0,
  "locked_at": "2024-01-15T10:05:00Z",
  "locked_by": "ObjectId"
}
```

### Attendance Entries
```json
{
  "_id": "ObjectId",
  "organization_id": "ObjectId",
  "session_id": "ObjectId",
  "student_id": "ObjectId",
  "user_id": "ObjectId",
  "status": "present",
  "marked_at": "2024-01-15T09:02:00Z",
  "marked_by": "ObjectId",
  "edited_at": null,
  "edited_by": null
}
```

---

## API Documentation

### Authentication Endpoints

```
POST /api/auth/login
POST /api/auth/register
GET /api/auth/me
POST /api/auth/logout
```

### Student Endpoints

```
GET /api/students/students
GET /api/students/students/{id}
```

### Faculty Endpoints

```
POST /api/faculty/faculty
GET /api/faculty/faculty
GET /api/faculty/faculty/{id}
PUT /api/faculty/faculty/{id}
DELETE /api/faculty/faculty/{id}
```

### Attendance Endpoints

```
POST /api/attendance/sessions          - Create session
GET /api/attendance/sessions/{id}      - Get session
POST /api/attendance/sessions/{id}/mark - Mark attendance
POST /api/attendance/sessions/{id}/lock - Lock session
```

### Reports Endpoints

```
GET /api/reports/attendance/student/{id}/summary
GET /api/reports/attendance/subject/{id}/report
POST /api/reports/exports              - Create export
GET /api/reports/exports/{id}          - Get export status
```

---

## Features by Role

### 🎓 Student

**Dashboard**
- Overall attendance summary (%)
- Subject-wise attendance breakdown
- Eligibility status (75%+ required)
- Color-coded attendance indicators

**My Attendance**
- View attendance for each subject
- See present/absent/leave records
- Export personal attendance report

**Timetable**
- View personal class schedule
- Get location and time for each class

### 👨‍🏫 Faculty

**Dashboard**
- Today's class schedule
- Quick action buttons
- Session statistics

**Mark Attendance**
- Select subject, batch, date, time
- Load student list automatically
- Mark present/absent/leave per student
- Bulk actions: "Mark All Present"
- Submit and lock session

**Attendance History**
- View all past sessions
- Edit (with time window limit)
- Unlock (with admin approval)
- Export session data

**Reports**
- Subject-wise attendance trends
- Student performance analysis

### 🧑‍💼 Admin (Org Admin)

**Dashboard**
- KPI cards (students, faculty, subjects, batches)
- Quick management actions

**Student Management**
- Add individual students
- Bulk import from CSV
- Edit student details
- Deactivate students
- View all students

**Faculty Management**
- Add faculty members
- Assign subjects
- Assign batches
- View faculty details
- Manage leaves

**Timetable Management**
- Create class schedules
- Check for conflicts (room, faculty)
- View all timetables
- Edit/delete timetables

**Attendance Control**
- View all attendance sessions
- Lock/unlock sessions
- Override attendance
- Export attendance data

**Reports & Analytics**
- Daily attendance report
- Subject-wise attendance
- Student-wise attendance
- Export to Excel/PDF

**Audit Logs**
- View all system actions
- Filter by user/action/date
- Track changes

### 🔐 Super Admin

All permissions + Organization management

---

## Security

### Authentication
- **JWT with HS256**: Tokens contain user_id, email, role, organization_id
- **Bcrypt Password Hashing**: All passwords hashed with bcrypt
- **Token Expiry**: 24-hour access tokens
- **Header Validation**: Bearer token required in Authorization header

### Authorization
- **Organization Isolation**: All queries filtered by organization_id
- **Role-Based Access Control**: Granular permissions per role
- **Immutable Records**: Attendance sessions locked after marking
- **Soft Deletes**: No data permanently deleted

### Audit Trail
- All critical actions logged with:
  - User ID
  - Action type
  - Resource ID
  - Timestamp
  - IP address
  - Changes made

### Data Validation
- Email validation with email-validator
- Input sanitization with Pydantic
- Type checking on all inputs
- CORS protection

---

## Deployment

### Environment Variables

```
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net
DB_NAME=attendance_system
SECRET_KEY=super-secret-key
VERCEL=1 (for Vercel deployment)
PORT=8000
```

### Docker Setup

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Vercel Deployment (Frontend)

```bash
npm run build
vercel deploy
```

---

## API Response Format

### Success Response
```json
{
  "message": "Operation successful",
  "data": {}
}
```

### Error Response
```json
{
  "detail": "Error message",
  "status": 400
}
```

---

## Testing

### Backend Test
```bash
pytest backend/
```

### Frontend Test
```bash
npm test
```

---

## Support

For issues or questions, contact: support@university.edu

**Version**: 2.0.0  
**Last Updated**: January 2024  
**License**: MIT
