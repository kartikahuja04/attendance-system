# Attendance Management System with QR Code

A comprehensive web-based attendance management system for teachers with QR code functionality, session management, and Excel export capabilities.

## Features

### Teacher Portal
1. **Login System**: Secure authentication for teachers
2. **Dashboard**: Easy navigation to mark or view attendance
3. **Mark Attendance**: 
   - Create sessions with class, subject, section, and timing details
   - Generate dynamic QR codes for students to scan
   - Live attendance display during the session
   - Manual attendance marking for adjustments
   - End session functionality
4. **View Attendance**:
   - View all past and active sessions
   - See detailed attendance records with timestamps
   - Export attendance to Excel file
   - View session details (class, subject, section, timings, total present/absent)

### Student Features
- Scan QR code to mark attendance
- Simple student ID input form
- Real-time attendance confirmation

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python run.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Access the Application**:
   - Open your browser and navigate to: `http://localhost:8000`
   - Default login credentials:
     - Username: `admin`
     - Password: `admin123`

## Database

The application uses SQLite database (`attendance.db`) which is automatically created on first run. The database includes:

- **teachers**: Teacher accounts and credentials
- **sessions**: Session information (class, subject, section, timings)
- **attendance**: Attendance records with timestamps and marking method

## Usage

### For Teachers

1. **Login**: Use your credentials to access the teacher portal
2. **Start a Session**:
   - Click "Mark Attendance" from the dashboard
   - Fill in the session details (class, subject, section, start time)
   - Click "Start Session"
3. **During Session**:
   - Display the QR code to students
   - Monitor live attendance updates
   - Manually mark attendance if needed (for adjustments)
   - Click "End Session" when done
4. **View Attendance**:
   - Click "View Attendance" from the dashboard
   - Select a session to view details
   - Export to Excel if needed

### For Students

1. Scan the QR code displayed by the teacher
2. Enter your Student ID
3. Submit to mark attendance
4. Receive confirmation

## Project Structure

```
attendance-system-4/
├── backend/
│   ├── __init__.py
│   ├── db.py          # Database configuration and schema
│   └── main.py        # FastAPI application and routes
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── mark_attendance.html
│   ├── session.html
│   ├── view_attendance.html
│   ├── student_form.html
│   ├── attendance_marked.html
│   ├── already_marked.html
│   ├── error.html
│   └── session_ended.html
├── requirements.txt
├── run.py
└── README.md
```

## API Endpoints

### Authentication
- `GET /login` - Login page
- `POST /api/login` - Login API
- `GET /logout` - Logout

### Dashboard
- `GET /dashboard` - Teacher dashboard

### Sessions
- `GET /mark-attendance` - Mark attendance page
- `POST /api/sessions/create` - Create new session
- `GET /api/sessions` - Get all sessions
- `GET /api/sessions/active` - Get active sessions
- `POST /api/sessions/end` - End a session
- `GET /session/{session_id}` - Session page with QR code

### Attendance
- `GET /api/qr/{session_id}` - Generate QR code
- `GET /mark_attendance_form/{token}` - Student attendance form
- `GET /mark/{token}` - Mark attendance (QR code)
- `POST /api/attendance/manual` - Mark attendance manually
- `GET /api/attendance/{session_id}` - Get attendance for session
- `GET /api/attendance/view/{session_id}` - Get detailed attendance data
- `GET /api/attendance/export/{session_id}` - Export attendance to Excel

### View Attendance
- `GET /view-attendance` - View attendance page

## Security Features

- Password hashing using SHA-256
- Session-based authentication
- QR code tokens expire after 30 seconds
- QR codes refresh every 10 seconds
- Session validation for attendance marking

## Technologies Used

- **Backend**: FastAPI, Python
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **QR Code**: qrcode library
- **Excel Export**: openpyxl
- **Templates**: Jinja2

## Notes

- QR codes automatically refresh every 10 seconds for security
- Each QR code token expires after 30 seconds
- Teachers can manually mark attendance for adjustments
- All attendance records include timestamps and marking method (QR/Manual)
- Excel export includes session details and attendance list

## Default Credentials

- **Username**: admin
- **Password**: admin123

*Change the default password in production!*

## License

This project is open source and available for educational purposes.

