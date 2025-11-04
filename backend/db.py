import sqlite3

# SQLite Database (local file)
conn = sqlite3.connect("attendance.db", check_same_thread=False)
cursor = conn.cursor()

# Create attendance table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    student_id TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
