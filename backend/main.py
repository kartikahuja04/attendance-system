from sqlite3.dbapi2 import Timestamp
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import qrcode, io, base64, secrets
import os

from .db import conn, cursor

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Home page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Attendance System</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 20px;
                text-align: center;
            }
            .container { 
                display: flex; 
                flex-direction: column; 
                gap: 30px; 
                margin-top: 50px;
            }
            .card {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            input[type="text"] {
                padding: 8px;
                margin: 10px 0;
                width: 200px;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background-color: #45a049;
            }
            .instructions {
                text-align: left;
                margin: 30px 0;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <h1>📊 Attendance System</h1>
        
        <div class="container">
            <div class="card">
                <h2>Start New Session</h2>
                <form action="/start" method="GET">
                    <div>
                        <label for="session_id">Enter Session ID:</label><br>
                        <input type="text" id="session_id" name="session_id" required 
                               placeholder="e.g., CS101-Lecture1"><br>
                        <button type="submit">Start Session</button>
                    </div>
                </form>
            </div>

            <div class="card">
                <h2>View Attendance</h2>
                <form action="/view" method="GET">
                    <div>
                        <label for="view_session_id">Enter Session ID:</label><br>
                        <input type="text" id="view_session_id" name="session_id" required 
                               placeholder="e.g., CS101-Lecture1"><br>
                        <button type="submit">View Attendance</button>
                    </div>
                </form>
            </div>
        </div>

        <div class="instructions">
            <h3>How to use:</h3>
            <ol>
                <li><strong>For Teachers:</strong> Start a session with a unique ID, then show the QR code to students.</li>
                <li><strong>For Students:</strong> Scan the QR code with your device to mark attendance.</li>
                <li><strong>View Attendance:</strong> Enter the session ID to see who has checked in.</li>
            </ol>
            <p><em>Note: QR codes automatically refresh every 10 seconds for security.</em></p>
        </div>
    </body>
    </html>
    """

# Handle form submission for starting a session
@app.get("/start")
async def start_session_redirect(session_id: str):
    return RedirectResponse(url=f"/start/{session_id}", status_code=303)

# Handle form submission for viewing attendance
@app.get("/view")
async def view_attendance_redirect(session_id: str):
    return RedirectResponse(url=f"/view/{session_id}", status_code=303)

# Teacher screen with dynamic QR refresh
@app.get("/start/{session_id}", response_class=HTMLResponse)
def start_session(session_id: str, request: Request):

    # Generate new nonce each refresh
    nonce = secrets.token_hex(4)
    expiry = datetime.utcnow() + timedelta(seconds=30)  # Increased to 30 seconds
    token = f"{session_id}:{nonce}:{int(expiry.timestamp())}"
    
    # Determine base URL: prefer public BASE_URL env (for tunnels/deployments), else current request host
    base_url = os.getenv("BASE_URL") or str(request.base_url).rstrip("/")
    # Create a URL that will prompt for student ID
    mark_url = f"{base_url}/mark_attendance_form/{token}"
    
    # For debugging
    print(f"Generated token: {token}")
    print(f"Mark URL: {mark_url}")

    # Create QR code with the full URL
    qr = qrcode.make(mark_url)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    # Auto-refresh QR every 10 seconds
    return f"""
    <html>
    <head><title>Attendance Session</title></head>
    <body style="font-family:Arial; text-align:center;">
        <h2>Session: {session_id}</h2>
        <p>Scan QR to mark attendance</p>
        <img src="data:image/png;base64,{img_b64}" width="220" style="border:2px solid black;">
        <div id="qr-countdown" style="margin-top:8px; font-weight:600; color:#e63946;"></div>
        <p style="margin-top:10px; font-size:12px; color:#555;">If scanning fails, open this URL directly:<br>
           <a href="{mark_url}">{mark_url}</a>
        </p>
        <div style="max-width:800px; margin:20px auto; text-align:left;">
            <h3 style="margin-bottom:8px;">Live Attendance</h3>
            <div id="att-count" style="margin-bottom:8px; color:#333;">Loading...</div>
            <table id="att-table" style="width:100%; border-collapse:collapse;">
                <thead>
                    <tr>
                        <th style="text-align:left; border-bottom:1px solid #ddd; padding:8px;">Student ID</th>
                        <th style="text-align:left; border-bottom:1px solid #ddd; padding:8px;">Time</th>
                    </tr>
                </thead>
                <tbody id="att-body"></tbody>
            </table>
        </div>
        <script>
            // QR refresh countdown (10 seconds)
            let qrTimeLeft = 10;
            const qrCountdownEl = document.getElementById('qr-countdown');
            function updateQrCountdown() {{
                if (qrCountdownEl) {{
                    qrCountdownEl.textContent = 'QR refreshes in ' + qrTimeLeft + 's';
                }}
                qrTimeLeft--;
                if (qrTimeLeft < 0) qrTimeLeft = 0;
            }}
            updateQrCountdown();
            const qrCountdownTimer = setInterval(updateQrCountdown, 1000);
            setTimeout(() => {{ clearInterval(qrCountdownTimer); window.location.reload(); }}, 10000);
            async function loadAttendance() {{
                try {{
                    const res = await fetch('/api/attendance/{session_id}');
                    const data = await res.json();
                    document.getElementById('att-count').textContent = 'Total Records: ' + data.total;
                    const tbody = document.getElementById('att-body');
                    tbody.innerHTML = '';
                    for (const row of data.records) {{
                        const tr = document.createElement('tr');
                        tr.innerHTML = '<td style="padding:8px; border-bottom:1px solid #eee;">' + row.student_id + '</td>' +
                                       '<td style="padding:8px; border-bottom:1px solid #eee;">' + row.timestamp + '</td>';
                        tbody.appendChild(tr);
                    }}
                }} catch (e) {{
                    document.getElementById('att-count').textContent = 'Failed to load attendance';
                }}
            }}
            loadAttendance();
            setInterval(loadAttendance, 3000);
        </script>
    </body>
    </html>
    """

# Form to enter student ID
@app.get("/mark_attendance_form/{token}", response_class=HTMLResponse)
async def mark_attendance_form(token: str):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mark Attendance</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                height: 100vh; 
                margin: 0; 
                background-color: #f0f8ff;
            }}
            .form-container {{ 
                background: white; 
                padding: 30px; 
                border-radius: 10px; 
                box-shadow: 0 0 10px rgba(0,0,0,0.1); 
                text-align: center;
            }}
            input[type="text"] {{ 
                padding: 10px; 
                margin: 10px 0; 
                width: 200px; 
                font-size: 16px;
            }}
            button {{ 
                background: #4CAF50; 
                color: white; 
                border: none; 
                padding: 10px 20px; 
                border-radius: 5px; 
                cursor: pointer;
                font-size: 16px;
            }}
            button:hover {{ background: #45a049; }}
        </style>
    </head>
    <body>
        <div class="form-container">
            <h2>Mark Your Attendance</h2>
            <form action="/mark/{token}" method="get">
                <div>
                    <label for="student_id">Enter your Student ID:</label><br>
                    <input type="text" id="student_id" name="student_id" required 
                           placeholder="e.g., S12345"><br>
                    <button type="submit">Submit</button>
                </div>
            </form>
        </div>
    </body>
    </html>
    """

# Student attendance marking API
@app.get("/mark/{token}", response_class=HTMLResponse)
async def mark_attendance(token: str, student_id: str):
    print(f"Marking attendance - Token: {token}, Student ID: {student_id}")
    
    try:
        session_id, nonce, expiry = token.split(":")
        print(f"Session: {session_id}, Nonce: {nonce}, Expiry: {expiry}")
    except Exception as e:
        error_msg = f"Invalid token format: {str(e)}"
        print(error_msg)
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body style=\"font-family:Arial; text-align:center; padding:50px; background:#fff3f3;\">
            <h2>Invalid QR Link</h2>
            <p>{error_msg}</p>
            <a href=\"/\" style=\"display:inline-block; margin-top:20px; padding:10px 20px; background:#4CAF50; color:#fff; text-decoration:none; border-radius:5px;\">Back to Home</a>
        </body>
        </html>
        """, status_code=400)

    # Validate expiry
    current_time = datetime.utcnow().timestamp()
    expiry_time = float(expiry)
    
    print(f"Current time: {current_time}, Expiry time: {expiry_time}")
    
    if current_time > expiry_time:
        print("Token expired")
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>QR Expired</title></head>
        <body style=\"font-family:Arial; text-align:center; padding:50px; background:#fff8e1;\">
            <h2>QR Code Expired</h2>
            <p>Please go back and scan a fresh QR code from the teacher's screen.</p>
            <a href=\"/\" style=\"display:inline-block; margin-top:20px; padding:10px 20px; background:#4CAF50; color:#fff; text-decoration:none; border-radius:5px;\">Back to Home</a>
        </body>
        </html>
        """, status_code=410)
    
    # Mark attendance
    try:
        # Check if already marked
        cursor.execute(
            "SELECT id FROM attendance WHERE session_id=? AND student_id=?",
            (session_id, student_id)
        )
        
        if cursor.fetchone():
            print(f"Attendance already marked for {student_id} in session {session_id}")
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Already Marked</title>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        display: flex; 
                        justify-content: center; 
                        align-items: center; 
                        height: 100vh; 
                        margin: 0; 
                        background-color: #fff3f3;
                    }}
                    .message-box {{ 
                        background: white; 
                        padding: 30px; 
                        border-radius: 10px; 
                        box-shadow: 0 0 10px rgba(0,0,0,0.1); 
                        text-align: center;
                        max-width: 400px;
                    }}
                    .tick {{ color: #ff9800; font-size: 50px; }}
                    .button {{ 
                        display: inline-block; 
                        margin-top: 20px; 
                        padding: 10px 20px; 
                        background: #4CAF50; 
                        color: white; 
                        text-decoration: none; 
                        border-radius: 5px;
                    }}
                </style>
            </head>
            <body>
                <div class="message-box">
                    <div class="tick">ℹ️</div>
                    <h2>Already Marked</h2>
                    <p>Your attendance was already recorded for this session.</p>
                    <p><strong>Student ID:</strong> {student_id}</p>
                    <p><strong>Session:</strong> {session_id}</p>
                    <a href="/" class="button">Back to Home</a>
                </div>
            </body>
            </html>
            """
        
        # Mark attendance
        cursor.execute(
            "INSERT INTO attendance (session_id, student_id) VALUES (?, ?)",
            (session_id, student_id)
        )
        conn.commit()
        
        print(f"Successfully marked attendance for {student_id} in session {session_id}")
        
        # Return a simple HTML response that will be shown in the browser
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Attendance Marked</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px;
                    background-color: #f0f8ff;
                }}
                .success-box {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    display: inline-block;
                    margin-top: 50px;
                }}
                .tick {{
                    color: #4CAF50;
                    font-size: 60px;
                    margin-bottom: 20px;
                }}
                .button {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 10px 20px;
                    background: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="success-box">
                <div class="tick">✓</div>
                <h2>Attendance Marked Successfully!</h2>
                <p>Student ID: {student_id}</p>
                <p>Session: {session_id}</p>
                <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <a href="/" class="button">Back to Home</a>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        error_msg = f"Error marking attendance: {str(e)}"
        print(error_msg)
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>Server Error</title></head>
        <body style=\"font-family:Arial; text-align:center; padding:50px; background:#fff3f3;\">
            <h2>Internal Server Error</h2>
            <p>{error_msg}</p>
            <a href=\"/\" style=\"display:inline-block; margin-top:20px; padding:10px 20px; background:#4CAF50; color:#fff; text-decoration:none; border-radius:5px;\">Back to Home</a>
        </body>
        </html>
        """, status_code=500)

# Live attendance JSON API
@app.get("/api/attendance/{session_id}")
def api_attendance(session_id: str):
    cursor.execute(
        """
        SELECT student_id,
               strftime('%Y-%m-%d %H:%M:%S', timestamp) as formatted_time
        FROM attendance
        WHERE session_id=?
        ORDER BY timestamp DESC
        """,
        (session_id,),
    )
    rows = cursor.fetchall()
    records = [
        {"student_id": sid, "timestamp": ts}
        for (sid, ts) in rows
    ]
    return JSONResponse({"session": session_id, "total": len(records), "records": records})

# View attendance (for teacher)
@app.get("/view/{session_id}", response_class=HTMLResponse)
def view_attendance(session_id: str):
    cursor.execute("""
        SELECT student_id, 
               strftime('%Y-%m-%d %H:%M:%S', timestamp) as formatted_time 
        FROM attendance 
        WHERE session_id=?
        ORDER BY timestamp DESC
    """, (session_id,))
    
    records = cursor.fetchall()
    
    # Create an HTML response
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Attendance for {session_id}</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #333; }}
            .back-button {{ 
                display: inline-block; 
                margin-bottom: 20px; 
                padding: 8px 16px; 
                background: #4CAF50; 
                color: white; 
                text-decoration: none; 
                border-radius: 4px;
            }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 20px;
            }}
            th, td {{ 
                padding: 12px; 
                text-align: left; 
                border-bottom: 1px solid #ddd;
            }}
            th {{ 
                background-color: #f2f2f2; 
                font-weight: bold;
            }}
            tr:hover {{ background-color: #f5f5f5; }}
        </style>
    </head>
    <body>
        <a href="/" class="back-button">← Back to Home</a>
        <h1>Attendance for Session: {session_id}</h1>
        <p>Total Records: {len(records)}</p>
    """
    
    if records:
        html_content += """
        <table>
            <tr>
                <th>Student ID</th>
                <th>Time</th>
            </tr>
        """
        for student_id, timestamp in records:
            html_content += f"""
            <tr>
                <td>{student_id}</td>
                <td>{timestamp}</td>
            </tr>
            """
        html_content += "</table>"
    else:
        html_content += "<p>No attendance records found for this session.</p>"
    
    html_content += """
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content, status_code=200)
