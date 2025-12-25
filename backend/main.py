from fastapi import FastAPI, Request, Form, HTTPException, Depends, Cookie, UploadFile, File, Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import qrcode, io, base64, secrets
import os
import hmac
import hashlib
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from typing import Optional
import shutil
import uuid

try:
    from backend.db import conn, cursor
except Exception:  # fallback when executed within the package context
    from .db import conn, cursor

app = FastAPI()

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve absolute paths for static and templates based on project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates")
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")

# Create uploads directories if they don't exist
os.makedirs(os.path.join(UPLOADS_DIR, "profile_pictures"), exist_ok=True)
os.makedirs(os.path.join(UPLOADS_DIR, "resumes"), exist_ok=True)

# Mount static files (directories are expected to exist in the deployment bundle)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Simple session management (in production, use proper JWT tokens)
async def get_current_teacher(
    session_token: Optional[str] = Cookie(None),
    x_auth_token: Optional[str] = Header(None, alias="X-Auth-Token")
):
    # Try cookie first, then header
    token = session_token or x_auth_token
    if not token:
        return None
    try:
        # Use a local cursor for thread safety if necessary, but in async def 
        # it runs in the main loop sequentially.
        cursor.execute("SELECT id, username FROM teachers WHERE id=?", (token,))
        teacher = cursor.fetchone()
        return {"id": teacher[0], "username": teacher[1]} if teacher else None
    except Exception as e:
        print(f"Auth error: {e}")
        return None

# Helper to normalize datetime values for JSON responses
def _ts_str(v):
    try:
        if hasattr(v, 'strftime'):
            return v.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        pass
    return str(v)

# Health check
@app.get("/api/health")
async def health():
    try:
        # Surface DB init errors clearly
        from backend.db import DB_INIT_ERROR  # type: ignore
        if DB_INIT_ERROR:
            raise RuntimeError(f"DB_INIT_ERROR: {DB_INIT_ERROR}")
        cursor.execute("SELECT 1")
        _ = cursor.fetchone()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"health_failed: {e}")

# Home page - redirect to login
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return RedirectResponse(url="/login", status_code=303)

# Login page
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Login API
@app.post("/api/login")
async def login(username: str = Form(...), password: str = Form(...)):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute(
        "SELECT id, username FROM teachers WHERE username=? AND password_hash=?",
        (username, password_hash)
    )
    teacher = cursor.fetchone()
    
    if teacher:
        # Return JSON for React app instead of redirect
        response = JSONResponse(content={
            "success": True,
            "message": "Login successful",
            "user": {"id": teacher[0], "username": teacher[1]}
        })
        # Set cookie for authentication - use SameSite=None for proxy compatibility
        response.set_cookie(
            key="session_token",
            value=str(teacher[0]),
            httponly=False,  # Allow JavaScript to read cookie
            samesite="none",  # Required for cross-port proxy
            secure=False,  # HTTP for localhost (browsers allow this for localhost)
            max_age=86400,
            path="/"
        )
        return response
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Logout
@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="session_token")
    return response

# Dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("dashboard.html", {"request": request, "teacher": teacher})

# Get teacher's schedule for today
@app.get("/api/teacher/schedule")
async def get_teacher_schedule(teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get today's day of week
    today = datetime.now().strftime('%A')
    
    # Query real schedule from database
    cursor.execute("""
        SELECT subject, subject_code, class_name, section, 
               start_time || '-' || end_time as time, room
        FROM schedules
        WHERE teacher_id=? AND day_of_week=?
        ORDER BY start_time
    """, (teacher["id"], today))
    
    rows = cursor.fetchall()
    schedule = [
        {
            'subject': r[0],
            'subject_code': r[1] or f"{r[2]}-{r[3]}",
            'class_name': r[2],
            'section': r[3],
            'time': r[4],
            'room': r[5]
        }
        for r in rows
    ]
    
    return JSONResponse({"schedule": schedule, "day": today})


# Get previous day statistics
@app.get("/api/teacher/previous-day-stats")
async def get_previous_day_stats(teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get yesterday's date
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Query sessions from yesterday
    cursor.execute("""
        SELECT s.subject, s.class_name, s.section, s.session_id
        FROM sessions s
        WHERE teacher_id=? AND DATE(start_time)=? AND status='ended'
        ORDER BY start_time
    """, (teacher["id"], yesterday))
    
    sessions = cursor.fetchall()
    stats = []
    
    for session in sessions:
        subject, class_name, section, session_id = session
        subject_code = f"{class_name}-{section}"
        
        # Get attendance count for this session
        cursor.execute("""
            SELECT COUNT(DISTINCT student_id) as present
            FROM attendance
            WHERE session_id=?
        """, (session_id,))
        present_count = cursor.fetchone()[0] or 0
        
        # Get total students from class_rosters table
        cursor.execute("""
            SELECT COUNT(*) FROM class_rosters
            WHERE class_name=? AND section=?
        """, (class_name, section))
        total_students = cursor.fetchone()[0] or 0
        
        # If no roster exists, estimate from attendance
        if total_students == 0:
            total_students = max(present_count, 30)  # Minimum 30 students
        
        absent_students = max(0, total_students - present_count)
        
        stats.append({
            'subject': subject,
            'subject_code': subject_code,
            'total_students': total_students,
            'present_students': present_count,
            'absent_students': absent_students
        })
    
    return JSONResponse({"stats": stats, "date": yesterday})


# ==================== ANNOUNCEMENTS ====================

# Get announcements
@app.get("/api/announcements")
async def get_announcements(teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor.execute("""
        SELECT id, title, content, priority, created_at
        FROM announcements
        WHERE expires_at IS NULL OR expires_at > datetime('now')
        ORDER BY priority DESC, created_at DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    return JSONResponse({"announcements": [
        {"id": r[0], "title": r[1], "content": r[2], 
         "priority": r[3], "date": _ts_str(r[4])}
        for r in rows
    ]})

# Create announcement
@app.post("/api/announcements")
async def create_announcement(
    content: str = Form(...),
    title: str = Form(None),
    priority: str = Form("normal"),
    teacher: Optional[dict] = Depends(get_current_teacher)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor.execute("""
        INSERT INTO announcements (title, content, priority, created_by)
        VALUES (?, ?, ?, ?)
    """, (title, content, priority, teacher["id"]))
    conn.commit()
    return JSONResponse({"success": True, "message": "Announcement created"})

# Delete announcement
@app.delete("/api/announcements/{announcement_id}")
async def delete_announcement(
    announcement_id: int,
    teacher: Optional[dict] = Depends(get_current_teacher)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor.execute("DELETE FROM announcements WHERE id=?", (announcement_id,))
    conn.commit()
    return JSONResponse({"success": True})


# ==================== TEACHER STATS ====================

# Get dashboard statistics
@app.get("/api/teacher/stats")
async def get_teacher_stats(teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Total sessions
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE teacher_id=?", (teacher["id"],))
    total_sessions = cursor.fetchone()[0] or 0
    
    # Active sessions
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE teacher_id=? AND status='active'", (teacher["id"],))
    active_sessions = cursor.fetchone()[0] or 0
    
    # Today's classes count
    today = datetime.now().strftime('%A')
    cursor.execute("SELECT COUNT(*) FROM schedules WHERE teacher_id=? AND day_of_week=?", (teacher["id"], today))
    todays_classes = cursor.fetchone()[0] or 0
    
    # Average attendance (last 7 days)
    cursor.execute("""
        SELECT s.session_id, s.class_name, s.section
        FROM sessions s
        WHERE s.teacher_id = ? AND s.status = 'ended'
        AND s.start_time > datetime('now', '-7 days')
    """, (teacher["id"],))
    recent_sessions = cursor.fetchall()
    
    attendance_rates = []
    for session_id, class_name, section in recent_sessions:
        cursor.execute("SELECT COUNT(DISTINCT student_id) FROM attendance WHERE session_id=?", (session_id,))
        present = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM class_rosters WHERE class_name=? AND section=?", (class_name, section))
        total = cursor.fetchone()[0] or 0
        
        if total > 0:
            attendance_rates.append((present / total) * 100)
        elif present > 0:
            attendance_rates.append(100)  # All present students counted as 100%
    
    avg_attendance = round(sum(attendance_rates) / len(attendance_rates), 1) if attendance_rates else 0
    
    return JSONResponse({
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "avg_attendance": avg_attendance,
        "todays_classes": todays_classes
    })


# ==================== SCHEDULES CRUD ====================

# Get all schedules for a teacher
@app.get("/api/schedules")
async def get_all_schedules(teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor.execute("""
        SELECT id, day_of_week, subject, subject_code, class_name, section, 
               start_time, end_time, room
        FROM schedules
        WHERE teacher_id=?
        ORDER BY 
            CASE day_of_week 
                WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 
                WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 
                ELSE 7 END,
            start_time
    """, (teacher["id"],))
    
    rows = cursor.fetchall()
    return JSONResponse({"schedules": [
        {
            "id": r[0], "day_of_week": r[1], "subject": r[2], "subject_code": r[3],
            "class_name": r[4], "section": r[5], "start_time": r[6], "end_time": r[7], "room": r[8]
        }
        for r in rows
    ]})

# Create schedule entry
@app.post("/api/schedules")
async def create_schedule(
    day_of_week: str = Form(...),
    subject: str = Form(...),
    subject_code: str = Form(None),
    class_name: str = Form(...),
    section: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    room: str = Form(None),
    teacher: Optional[dict] = Depends(get_current_teacher)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor.execute("""
        INSERT INTO schedules (teacher_id, day_of_week, subject, subject_code, class_name, section, start_time, end_time, room)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (teacher["id"], day_of_week, subject, subject_code, class_name, section, start_time, end_time, room))
    conn.commit()
    return JSONResponse({"success": True, "id": cursor.lastrowid})

# Delete schedule entry
@app.delete("/api/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    teacher: Optional[dict] = Depends(get_current_teacher)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor.execute("DELETE FROM schedules WHERE id=? AND teacher_id=?", (schedule_id, teacher["id"]))
    conn.commit()
    return JSONResponse({"success": True})


# ==================== CLASS ROSTERS ====================

# Get unique classes from sessions
@app.get("/api/classes")
async def get_classes(teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor.execute("""
        SELECT DISTINCT class_name, section FROM sessions WHERE teacher_id=?
        UNION
        SELECT DISTINCT class_name, section FROM schedules WHERE teacher_id=?
        ORDER BY class_name, section
    """, (teacher["id"], teacher["id"]))
    
    return JSONResponse({"classes": [
        {"class_name": r[0], "section": r[1]} for r in cursor.fetchall()
    ]})

# Get students in a class
@app.get("/api/classes/{class_name}/{section}/students")
async def get_class_students(class_name: str, section: str, teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor.execute("""
        SELECT id, student_id, student_name FROM class_rosters
        WHERE class_name=? AND section=?
        ORDER BY student_id
    """, (class_name, section))
    
    return JSONResponse({"students": [
        {"id": r[0], "student_id": r[1], "student_name": r[2]} for r in cursor.fetchall()
    ]})

# Add student to roster
@app.post("/api/classes/{class_name}/{section}/students")
async def add_student_to_roster(
    class_name: str, 
    section: str,
    student_id: str = Form(...),
    student_name: str = Form(None),
    teacher: Optional[dict] = Depends(get_current_teacher)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        cursor.execute("""
            INSERT INTO class_rosters (class_name, section, student_id, student_name)
            VALUES (?, ?, ?, ?)
        """, (class_name, section, student_id, student_name))
        conn.commit()
        return JSONResponse({"success": True, "id": cursor.lastrowid})
    except Exception as e:
        raise HTTPException(status_code=400, detail="Student already exists in roster")

# Remove student from roster
@app.delete("/api/classes/{class_name}/{section}/students/{student_id}")
async def remove_student_from_roster(
    class_name: str,
    section: str,
    student_id: str,
    teacher: Optional[dict] = Depends(get_current_teacher)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor.execute("DELETE FROM class_rosters WHERE class_name=? AND section=? AND student_id=?", 
                   (class_name, section, student_id))
    conn.commit()
    return JSONResponse({"success": True})

# Bulk import students to roster
@app.post("/api/classes/{class_name}/{section}/students/bulk")
async def bulk_import_students(
    class_name: str,
    section: str,
    request: Request,
    teacher: Optional[dict] = Depends(get_current_teacher)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    students = data.get("students", [])
    imported = 0
    
    for student in students:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO class_rosters (class_name, section, student_id, student_name)
                VALUES (?, ?, ?, ?)
            """, (class_name, section, student.get("student_id"), student.get("student_name")))
            if cursor.rowcount > 0:
                imported += 1
        except:
            pass
    
    conn.commit()
    return JSONResponse({"success": True, "imported": imported, "total": len(students)})


# ==================== TEACHER PROFILE & DIRECTORY ====================


# Teacher Profile Page
@app.get("/teacher/profile", response_class=HTMLResponse)
async def teacher_profile_page(request: Request, teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        return RedirectResponse(url="/login", status_code=303)
    
    # Get full teacher profile
    cursor.execute("""
        SELECT id, username, employee_id, full_name, email, phone, department, designation,
               qualification, education, subjects_taught, research_areas, publications, bio,
               profile_picture_url, resume_url, linkedin_url, google_scholar_url, profile_visible
        FROM teachers WHERE id=?
    """, (teacher["id"],))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    profile = {
        "id": row[0],
        "username": row[1],
        "employee_id": row[2],
        "full_name": row[3],
        "email": row[4],
        "phone": row[5],
        "department": row[6],
        "designation": row[7],
        "qualification": row[8],
        "education": row[9],
        "subjects_taught": row[10],
        "research_areas": row[11],
        "publications": row[12],
        "bio": row[13],
        "profile_picture_url": row[14],
        "resume_url": row[15],
        "linkedin_url": row[16],
        "google_scholar_url": row[17],
        "profile_visible": row[18] if row[18] is not None else 1
    }
    
    return templates.TemplateResponse("teacher_profile.html", {"request": request, "profile": profile})

# Get Teacher Profile API
@app.get("/api/teacher/profile")
async def get_teacher_profile(teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor.execute("""
        SELECT id, username, employee_id, full_name, email, phone, department, designation,
               qualification, education, subjects_taught, research_areas, publications, bio,
               profile_picture_url, resume_url, linkedin_url, google_scholar_url, profile_visible
        FROM teachers WHERE id=?
    """, (teacher["id"],))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    profile = {
        "id": row[0],
        "username": row[1],
        "employee_id": row[2],
        "full_name": row[3],
        "email": row[4],
        "phone": row[5],
        "department": row[6],
        "designation": row[7],
        "qualification": row[8],
        "education": row[9],
        "subjects_taught": row[10],
        "research_areas": row[11],
        "publications": row[12],
        "bio": row[13],
        "profile_picture_url": row[14],
        "resume_url": row[15],
        "linkedin_url": row[16],
        "google_scholar_url": row[17],
        "profile_visible": row[18] if row[18] is not None else 1
    }
    
    return JSONResponse({"profile": profile})

# Update Teacher Profile
@app.post("/api/teacher/profile/update")
async def update_teacher_profile(
    request: Request,
    teacher: Optional[dict] = Depends(get_current_teacher),
    full_name: str = Form(None),
    employee_id: str = Form(None),
    email: str = Form(None),
    phone: str = Form(None),
    department: str = Form(None),
    designation: str = Form(None),
    qualification: str = Form(None),
    education: str = Form(None),
    subjects_taught: str = Form(None),
    research_areas: str = Form(None),
    publications: str = Form(None),
    bio: str = Form(None),
    linkedin_url: str = Form(None),
    google_scholar_url: str = Form(None)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        cursor.execute("""
            UPDATE teachers SET
                full_name=?, employee_id=?, email=?, phone=?, department=?, designation=?,
                qualification=?, education=?, subjects_taught=?, research_areas=?,
                publications=?, bio=?, linkedin_url=?, google_scholar_url=?
            WHERE id=?
        """, (full_name, employee_id, email, phone, department, designation,
              qualification, education, subjects_taught, research_areas,
              publications, bio, linkedin_url, google_scholar_url, teacher["id"]))
        conn.commit()
        
        return JSONResponse({"success": True, "message": "Profile updated successfully"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating profile: {str(e)}")

# Upload Profile Picture
@app.post("/api/teacher/profile/upload-photo")
async def upload_profile_picture(
    file: UploadFile = File(...),
    teacher: Optional[dict] = Depends(get_current_teacher)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPG, PNG, and WebP are allowed.")
    
    # Validate file size (5MB max)
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
    
    # Generate unique filename
    file_ext = file.filename.split('.')[-1]
    unique_filename = f"{teacher['id']}_{uuid.uuid4().hex[:8]}.{file_ext}"
    file_path = os.path.join(UPLOADS_DIR, "profile_pictures", unique_filename)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Update database
    profile_picture_url = f"/uploads/profile_pictures/{unique_filename}"
    cursor.execute("UPDATE teachers SET profile_picture_url=? WHERE id=?", (profile_picture_url, teacher["id"]))
    conn.commit()
    
    return JSONResponse({"success": True, "url": profile_picture_url})

# Upload Resume
@app.post("/api/teacher/profile/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    teacher: Optional[dict] = Depends(get_current_teacher)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Validate file type
    allowed_types = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOC, and DOCX are allowed.")
    
    # Validate file size (10MB max)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    # Generate unique filename
    file_ext = file.filename.split('.')[-1]
    unique_filename = f"{teacher['id']}_{uuid.uuid4().hex[:8]}.{file_ext}"
    file_path = os.path.join(UPLOADS_DIR, "resumes", unique_filename)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Update database
    resume_url = f"/uploads/resumes/{unique_filename}"
    cursor.execute("UPDATE teachers SET resume_url=? WHERE id=?", (resume_url, teacher["id"]))
    conn.commit()
    
    return JSONResponse({"success": True, "url": resume_url})

# Toggle Profile Visibility
@app.post("/api/teacher/profile/visibility")
async def toggle_profile_visibility(
    request: Request,
    teacher: Optional[dict] = Depends(get_current_teacher)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    visible = 1 if data.get("visible", True) else 0
    
    cursor.execute("UPDATE teachers SET profile_visible=? WHERE id=?", (visible, teacher["id"]))
    conn.commit()
    
    return JSONResponse({"success": True, "visible": visible == 1})

# Teacher Directory Page
@app.get("/teacher/directory", response_class=HTMLResponse)
async def teacher_directory_page(request: Request, teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("teacher_directory.html", {"request": request})

# Get All Teachers (Directory)
@app.get("/api/teachers/directory")
async def get_teachers_directory(teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get all teachers with visible profiles
    cursor.execute("""
        SELECT id, username, full_name, email, phone, department, designation,
               qualification, subjects_taught, research_areas, profile_picture_url, profile_visible
        FROM teachers
        WHERE profile_visible=1 OR id=?
        ORDER BY full_name, username
    """, (teacher["id"],))
    
    rows = cursor.fetchall()
    teachers = []
    
    for row in rows:
        teachers.append({
            "id": row[0],
            "username": row[1],
            "full_name": row[2],
            "email": row[3],
            "phone": row[4],
            "department": row[5],
            "designation": row[6],
            "qualification": row[7],
            "subjects_taught": row[8],
            "research_areas": row[9],
            "profile_picture_url": row[10],
            "profile_visible": row[11]
        })
    
    return JSONResponse({"teachers": teachers})

# Get Specific Teacher Profile
@app.get("/api/teachers/{teacher_id}/profile")
async def get_specific_teacher_profile(
    teacher_id: int,
    teacher: Optional[dict] = Depends(get_current_teacher)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor.execute("""
        SELECT id, username, full_name, email, phone, department, designation,
               qualification, education, subjects_taught, research_areas, publications, bio,
               profile_picture_url, linkedin_url, google_scholar_url, profile_visible
        FROM teachers WHERE id=?
    """, (teacher_id,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Check if profile is visible (or if it's the current user's own profile)
    if row[16] == 0 and row[0] != teacher["id"]:
        raise HTTPException(status_code=403, detail="Profile is not visible")
    
    teacher_data = {
        "id": row[0],
        "username": row[1],
        "full_name": row[2],
        "email": row[3],
        "phone": row[4],
        "department": row[5],
        "designation": row[6],
        "qualification": row[7],
        "education": row[8],
        "subjects_taught": row[9],
        "research_areas": row[10],
        "publications": row[11],
        "bio": row[12],
        "profile_picture_url": row[13],
        "linkedin_url": row[14],
        "google_scholar_url": row[15],
        "profile_visible": row[16]
    }
    
    return JSONResponse({"teacher": teacher_data})



# Get active sessions for teacher
@app.get("/api/sessions/active")
async def get_active_sessions(teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor.execute("""
        SELECT session_id, class_name, subject, section, start_time, status
        FROM sessions
        WHERE teacher_id=? AND status='active'
        ORDER BY start_time DESC
    """, (teacher["id"],))
    
    sessions = cursor.fetchall()
    return JSONResponse({
        "sessions": [
            {
                "id": s[0],              # React expectations
                "session_id": s[0],      # Jinja2 expectations
                "class_name": s[1],
                "subject": s[2],
                "subject_code": s[2],
                "section": s[3],
                "date": _ts_str(s[4]),    # React expectations
                "start_time": _ts_str(s[4]), # Jinja2 expectations
                "status": s[5]
            }
            for s in sessions
        ]
    })

# Get all sessions for teacher
@app.get("/api/sessions")
async def get_all_sessions(
    date: Optional[str] = None,
    teacher: Optional[dict] = Depends(get_current_teacher)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = "SELECT session_id, class_name, subject, section, start_time, end_time, status FROM sessions WHERE teacher_id=?"
    params = [teacher["id"]]
    
    if date:
        # Match YYYY-MM-DD
        query += " AND start_time LIKE ?"
        params.append(f"{date}%")
    
    query += " ORDER BY start_time DESC"
    
    cursor.execute(query, params)
    sessions = cursor.fetchall()
    
    return JSONResponse({
        "sessions": [
            {
                "id": s[0],              # For React
                "session_id": s[0],      # For Jinja2
                "class_name": s[1],
                "subject": s[2],
                "section": s[3],
                "date": _ts_str(s[4]),    # For React
                "start_time": _ts_str(s[4]), # For Jinja2
                "end_time": _ts_str(s[5]) if s[5] is not None else None,
                "status": s[6]
            }
            for s in sessions
        ]
    })

# Create new session
@app.post("/api/sessions/create")
async def create_session(
    class_name: str = Form(...),
    subject: str = Form(...),
    section: str = Form(...),
    start_time: str = Form(...),
    teacher: Optional[dict] = Depends(get_current_teacher)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Normalize start_time (replace 'T' from datetime-local with space)
    if start_time and 'T' in start_time:
        start_time = start_time.replace('T', ' ')
    
    # Generate unique session ID
    session_id = f"{class_name}-{subject}-{section}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    try:
        cursor.execute("""
            INSERT INTO sessions (session_id, teacher_id, class_name, subject, section, start_time, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
        """, (session_id, teacher["id"], class_name, subject, section, start_time))
        conn.commit()
        
        return JSONResponse({
            "success": True,
            "session_id": session_id,
            "message": "Session created successfully"
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating session: {str(e)}")

# End session
@app.post("/api/sessions/end")
async def end_session(
    session_id: str = Form(...),
    teacher: Optional[dict] = Depends(get_current_teacher)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Verify session belongs to teacher
    cursor.execute("SELECT teacher_id FROM sessions WHERE session_id=?", (session_id,))
    session = cursor.fetchone()
    
    if not session or session[0] != teacher["id"]:
        raise HTTPException(status_code=403, detail="Session not found or access denied")
    
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        UPDATE sessions SET status='ended', end_time=? WHERE session_id=?
    """, (end_time, session_id))
    conn.commit()
    
    return JSONResponse({"success": True, "message": "Session ended successfully"})

# Mark Attendance page
@app.get("/mark-attendance", response_class=HTMLResponse)
async def mark_attendance_page(request: Request, teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("mark_attendance.html", {"request": request, "teacher": teacher})

# Start session page (QR code display)
@app.get("/session/{session_id}", response_class=HTMLResponse)
async def session_page(session_id: str, request: Request, teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        return RedirectResponse(url="/login", status_code=303)
    
    # Verify session belongs to teacher
    cursor.execute("""
        SELECT class_name, subject, section, start_time, status
        FROM sessions WHERE session_id=?
    """, (session_id,))
    session = cursor.fetchone()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session[4] != 'active':
        return templates.TemplateResponse("session_ended.html", {
            "request": request,
            "session_id": session_id
        })
    
    return templates.TemplateResponse("session.html", {
        "request": request,
        "session_id": session_id,
        "class_name": session[0],
        "subject": session[1],
        "section": session[2],
        "start_time": session[3]
    })

# Generate QR code API
@app.get("/api/qr/{session_id}")
async def generate_qr(session_id: str, request: Request):
    # Generate new nonce each refresh
    nonce = secrets.token_hex(4)
    expiry = datetime.utcnow() + timedelta(seconds=30)
    token_payload = f"{session_id}:{nonce}:{int(expiry.timestamp())}"
    secret = (os.getenv("SECRET_KEY") or "change-me").encode()
    signature = hmac.new(secret, token_payload.encode(), hashlib.sha256).hexdigest()
    token = f"{token_payload}:{signature}"
    
    # Determine base URL
    base_url = os.getenv("BASE_URL") or str(request.base_url).rstrip("/")
    mark_url = f"{base_url}/mark_attendance_form/{token}"
    
    # Create QR code
    qr = qrcode.make(mark_url)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()
    
    return JSONResponse({
        "qr_code": f"data:image/png;base64,{img_b64}",
        "mark_url": mark_url,
        "token": token
    })

# Form to enter student ID
@app.get("/mark_attendance_form/{token}", response_class=HTMLResponse)
async def mark_attendance_form(token: str, request: Request):
    return templates.TemplateResponse("student_form.html", {"request": request, "token": token})

# Student attendance marking API
@app.get("/mark/{token}", response_class=HTMLResponse)
async def mark_attendance(token: str, student_id: str, request: Request):
    try:
        parts = token.split(":")
        if len(parts) == 4:
            session_id, nonce, expiry, signature = parts
            token_payload = f"{session_id}:{nonce}:{expiry}"
            secret = (os.getenv("SECRET_KEY") or "change-me").encode()
            expected_sig = hmac.new(secret, token_payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected_sig):
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "error": "Invalid QR token signature"
                })
        elif len(parts) == 3:
            # Backwards compatibility (unsigned token)
            session_id, nonce, expiry = parts
        else:
            raise ValueError("Invalid token format")
    except:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Invalid token format"
        })
    
    # Validate expiry
    current_time = datetime.utcnow().timestamp()
    expiry_time = float(expiry)
    
    if current_time > expiry_time:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "QR code expired. Please scan a fresh QR code."
        })
    
    # Check if session is active (allow bypass in serverless demo)
    if os.getenv("ALLOW_MARK_WITHOUT_SESSION") == "1":
        session = ("active",)
    else:
        cursor.execute("SELECT status FROM sessions WHERE session_id=?", (session_id,))
        session = cursor.fetchone()
        if not session or session[0] != 'active':
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Session is not active"
            })
    
    # Mark attendance
    try:
        # Check if already marked
        cursor.execute(
            "SELECT id FROM attendance WHERE session_id=? AND student_id=?",
            (session_id, student_id)
        )
        
        if cursor.fetchone():
            return templates.TemplateResponse("already_marked.html", {
                "request": request,
                "student_id": student_id,
                "session_id": session_id
            })
        
        # Mark attendance
        cursor.execute(
            "INSERT INTO attendance (session_id, student_id, marked_by) VALUES (?, ?, 'qr')",
            (session_id, student_id)
        )
        conn.commit()
        
        return templates.TemplateResponse("attendance_marked.html", {
            "request": request,
            "student_id": student_id,
            "session_id": session_id,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error marking attendance: {str(e)}"
        })

# Manual attendance marking
@app.post("/api/attendance/manual")
async def mark_attendance_manual(
    session_id: str = Form(...),
    student_id: str = Form(...),
    teacher: Optional[dict] = Depends(get_current_teacher)
):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Verify session belongs to teacher
    cursor.execute("SELECT teacher_id, status FROM sessions WHERE session_id=?", (session_id,))
    session = cursor.fetchone()
    
    if not session or session[0] != teacher["id"]:
        raise HTTPException(status_code=403, detail="Session not found or access denied")
    
    if session[1] != 'active':
        raise HTTPException(status_code=400, detail="Session is not active")
    
    try:
        # Check if already marked
        cursor.execute(
            "SELECT id FROM attendance WHERE session_id=? AND student_id=?",
            (session_id, student_id)
        )
        
        if cursor.fetchone():
            return JSONResponse({"success": False, "message": "Attendance already marked"})
        
        # Mark attendance
        cursor.execute(
            "INSERT INTO attendance (session_id, student_id, marked_by) VALUES (?, ?, 'manual')",
            (session_id, student_id)
        )
        conn.commit()
        
        return JSONResponse({"success": True, "message": "Attendance marked successfully"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

# Live attendance JSON API
@app.get("/api/attendance/{session_id}")
async def api_attendance(session_id: str):
    cursor.execute(
        """
        SELECT student_id, timestamp, marked_by
        FROM attendance
        WHERE session_id=?
        ORDER BY timestamp DESC
        """,
        (session_id,),
    )
    rows = cursor.fetchall()
    norm = []
    for (sid, ts, mb) in rows:
        if hasattr(ts, 'strftime'):
            ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
        else:
            ts_str = str(ts)
        norm.append({"student_id": sid, "timestamp": ts_str, "marked_by": mb})
    return JSONResponse({
        "session": session_id,
        "total": len(norm),
        "records": norm
    })

# Student attendance history API (for QuickMark mobile app)
@app.get("/api/attendance/history/{student_id}")
async def get_student_attendance_history(student_id: str):
    """Get attendance history for a specific student."""
    cursor.execute("""
        SELECT a.session_id, a.timestamp, a.marked_by,
               s.class_name, s.subject, s.section
        FROM attendance a
        LEFT JOIN sessions s ON a.session_id = s.session_id
        WHERE a.student_id = ?
        ORDER BY a.timestamp DESC
        LIMIT 100
    """, (student_id,))
    
    rows = cursor.fetchall()
    records = []
    for row in rows:
        records.append({
            "session_id": row[0],
            "timestamp": _ts_str(row[1]),
            "marked_by": row[2],
            "class_name": row[3],
            "subject": row[4],
            "section": row[5],
            "status": "Present"
        })
    
    return JSONResponse({"records": records})

# View Attendance page
@app.get("/view-attendance", response_class=HTMLResponse)
async def view_attendance_page(request: Request, teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("view_attendance.html", {"request": request, "teacher": teacher})

# Get attendance for a session
@app.get("/api/attendance/view/{session_id}")
async def get_attendance_data(session_id: str, teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get session details
    cursor.execute("""
        SELECT class_name, subject, section, start_time, end_time, status
        FROM sessions
        WHERE session_id=? AND teacher_id=?
    """, (session_id, teacher["id"]))
    
    session = cursor.fetchone()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get attendance records (format timestamps in Python)
    cursor.execute(
        """
        SELECT student_id, timestamp, marked_by
        FROM attendance
        WHERE session_id=?
        ORDER BY timestamp DESC
        """,
        (session_id,),
    )
    records = cursor.fetchall()
    attendance_list = [
        {"student_id": r[0], "timestamp": r[1], "marked_by": r[2]}
        for r in records
    ]
    
    # Get unique student count
    cursor.execute("""
        SELECT COUNT(DISTINCT student_id) FROM attendance WHERE session_id=?
    """, (session_id,))
    total_present = cursor.fetchone()[0]
    
    # Calculate absent count using class_roster
    cursor.execute("""
        SELECT COUNT(*) FROM class_rosters 
        WHERE class_name=? AND section=?
    """, (session[0], session[2]))
    total_roster = cursor.fetchone()[0]
    total_absent = max(0, total_roster - total_present)
    
    return JSONResponse({
        "session": {
            "session_id": session_id,
            "class_name": session[0],
            "subject": session[1],
            "section": session[2],
            "start_time": _ts_str(session[3]),
            "end_time": _ts_str(session[4]) if session[4] is not None else None,
            "status": session[5]
        },
        "attendance": [
            {"student_id": a["student_id"], "timestamp": _ts_str(a["timestamp"]), "marked_by": a["marked_by"]}
            for a in attendance_list
        ],
        "total_present": total_present,
        "total_absent": total_absent
    })

# Export attendance to Excel
@app.get("/api/attendance/export/{session_id}")
async def export_attendance(session_id: str, teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get session details
    cursor.execute("""
        SELECT class_name, subject, section, start_time, end_time
        FROM sessions
        WHERE session_id=? AND teacher_id=?
    """, (session_id, teacher["id"]))
    
    session = cursor.fetchone()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get attendance records (format timestamps in Python for cross-DB compatibility)
    cursor.execute(
        """
        SELECT student_id, timestamp, marked_by
        FROM attendance
        WHERE session_id=?
        ORDER BY timestamp DESC
        """,
        (session_id,)
    )
    
    records = cursor.fetchall()
    
    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance"
    
    # Header style
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=12)
    
    # Session info
    ws['A1'] = "Class"
    ws['B1'] = session[0]
    ws['A2'] = "Subject"
    ws['B2'] = session[1]
    ws['A3'] = "Section"
    ws['B3'] = session[2]
    ws['A4'] = "Start Time"
    ws['B4'] = _ts_str(session[3])
    ws['A5'] = "End Time"
    ws['B5'] = _ts_str(session[4]) if session[4] else "N/A"
    ws['A6'] = "Total Present"
    ws['B6'] = len(records)
    
    # Attendance table header
    ws['A8'] = "Student ID"
    ws['B8'] = "Timestamp"
    ws['C8'] = "Marked By"
    
    for col in ['A8', 'B8', 'C8']:
        ws[col].fill = header_fill
        ws[col].font = header_font
        ws[col].alignment = Alignment(horizontal="center")
    
    # Attendance data
    from datetime import datetime as _dt
    for idx, record in enumerate(records, start=9):
        sid, ts, mb = record[0], record[1], record[2]
        # Normalize timestamp to string
        if hasattr(ts, 'strftime'):
            ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
        else:
            # SQLite may store as string already
            ts_str = str(ts)
        ws[f'A{idx}'] = sid
        ws[f'B{idx}'] = ts_str
        ws[f'C{idx}'] = mb
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 15
    
    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    # Return file
    filename = f"attendance_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}"
    }
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )
