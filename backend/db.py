import sqlite3
import hashlib

# SQLite Database (local file)
conn = sqlite3.connect("attendance.db", check_same_thread=False)
cursor = conn.cursor()

# Create teachers table
cursor.execute("""
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Create sessions table
cursor.execute("""
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    teacher_id INTEGER NOT NULL,
    class_name TEXT NOT NULL,
    subject TEXT NOT NULL,
    section TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
)
""")

# Create attendance table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    marked_by TEXT DEFAULT 'qr',
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
)
""")

# Migration: ensure 'marked_by' column exists on 'attendance'
# Older databases may be missing this column, causing 'no such column: marked_by'.
try:
    cursor.execute("PRAGMA table_info(attendance)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'marked_by' not in cols:
        cursor.execute("ALTER TABLE attendance ADD COLUMN marked_by TEXT DEFAULT 'qr'")
except Exception:
    pass

# Create default teacher account (username: admin, password: admin123)
# Password hash for 'admin123'
default_password_hash = hashlib.sha256("admin123".encode()).hexdigest()
cursor.execute("""
INSERT OR IGNORE INTO teachers (username, password_hash) 
VALUES ('admin', ?)
""", (default_password_hash,))

conn.commit()
