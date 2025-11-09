from fastapi import FastAPI, Request, Form, HTTPException, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import qrcode, io, base64, secrets
import os
import hashlib
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from typing import Optional

try:
    from backend.db import conn, cursor
except Exception:  # fallback when executed within the package context
    from .db import conn, cursor

app = FastAPI()

# Resolve absolute paths for static and templates based on project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates")

# Mount static files (directories are expected to exist in the deployment bundle)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Simple session management (in production, use proper JWT tokens)
def get_current_teacher(session_token: Optional[str] = Cookie(None)):
    if not session_token:
        return None
    try:
        cursor.execute("SELECT id, username FROM teachers WHERE id=?", (session_token,))
        teacher = cursor.fetchone()
        return {"id": teacher[0], "username": teacher[1]} if teacher else None
    except:
        return None

# Health check
@app.get("/api/health")
async def health():
    try:
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
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="session_token", value=str(teacher[0]), httponly=True)
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
                "session_id": s[0],
                "class_name": s[1],
                "subject": s[2],
                "section": s[3],
                "start_time": s[4],
                "status": s[5]
            }
            for s in sessions
        ]
    })

# Get all sessions for teacher
@app.get("/api/sessions")
async def get_all_sessions(teacher: Optional[dict] = Depends(get_current_teacher)):
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cursor.execute("""
        SELECT session_id, class_name, subject, section, start_time, end_time, status
        FROM sessions
        WHERE teacher_id=?
        ORDER BY start_time DESC
    """, (teacher["id"],))
    
    sessions = cursor.fetchall()
    return JSONResponse({
        "sessions": [
            {
                "session_id": s[0],
                "class_name": s[1],
                "subject": s[2],
                "section": s[3],
                "start_time": s[4],
                "end_time": s[5],
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
    token = f"{session_id}:{nonce}:{int(expiry.timestamp())}"
    
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
        session_id, nonce, expiry = token.split(":")
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
def api_attendance(session_id: str):
    cursor.execute("""
        SELECT student_id,
               strftime('%Y-%m-%d %H:%M:%S', timestamp) as formatted_time,
               marked_by
        FROM attendance
        WHERE session_id=?
        ORDER BY timestamp DESC
    """, (session_id,))
    
    rows = cursor.fetchall()
    records = [
        {"student_id": sid, "timestamp": ts, "marked_by": mb}
        for (sid, ts, mb) in rows
    ]
    return JSONResponse({
        "session": session_id,
        "total": len(records),
        "records": records
    })

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
    
    # Get attendance records
    cursor.execute("""
        SELECT student_id,
               strftime('%Y-%m-%d %H:%M:%S', timestamp) as formatted_time,
               marked_by
        FROM attendance
        WHERE session_id=?
        ORDER BY timestamp DESC
    """, (session_id,))
    
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
    
    return JSONResponse({
        "session": {
            "session_id": session_id,
            "class_name": session[0],
            "subject": session[1],
            "section": session[2],
            "start_time": session[3],
            "end_time": session[4],
            "status": session[5]
        },
        "attendance": attendance_list,
        "total_present": total_present,
        "total_absent": 0  # You can calculate this if you have a student list
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
    
    # Get attendance records
    cursor.execute("""
        SELECT student_id,
               strftime('%Y-%m-%d %H:%M:%S', timestamp) as formatted_time,
               marked_by
        FROM attendance
        WHERE session_id=?
        ORDER BY timestamp DESC
    """, (session_id,))
    
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
    ws['B4'] = session[3]
    ws['A5'] = "End Time"
    ws['B5'] = session[4] if session[4] else "N/A"
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
    for idx, record in enumerate(records, start=9):
        ws[f'A{idx}'] = record[0]
        ws[f'B{idx}'] = record[1]
        ws[f'C{idx}'] = record[2]
    
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
