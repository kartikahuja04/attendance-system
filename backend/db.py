import os
import sqlite3
import hashlib

USE_POSTGRES = bool(os.getenv("DATABASE_URL"))

# ---------------------------
# PASSWORD UTILS
# ---------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ---------------------------
# DATABASE CONNECTION
# ---------------------------
if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import DictCursor

    conn = psycopg2.connect(
        os.getenv("DATABASE_URL"),
        cursor_factory=DictCursor,
        sslmode="require"
    )
    conn.autocommit = True
    cursor = conn.cursor()
    Q = "%s"

else:
    db_path = os.getenv("DB_PATH", "attendance.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    Q = "?"

    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")

# ---------------------------
# USERS TABLE
# ---------------------------
if USE_POSTGRES:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('admin','teacher','student')),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    )
    """)
else:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('admin','teacher','student')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

# ---------------------------
# SESSIONS TABLE
# ---------------------------
if USE_POSTGRES:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id SERIAL PRIMARY KEY,
        session_id TEXT UNIQUE NOT NULL,
        teacher_id INTEGER NOT NULL REFERENCES users(id),
        class_name TEXT NOT NULL,
        subject TEXT NOT NULL,
        section TEXT NOT NULL,
        start_time TIMESTAMPTZ NOT NULL,
        end_time TIMESTAMPTZ,
        status TEXT DEFAULT 'active'
    )
    """)
else:
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
        FOREIGN KEY (teacher_id) REFERENCES users(id)
    )
    """)

# ---------------------------
# ATTENDANCE TABLE
# ---------------------------
if USE_POSTGRES:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id SERIAL PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES sessions(session_id),
        student_id TEXT NOT NULL,
        timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        marked_by TEXT DEFAULT 'qr',
        UNIQUE(session_id, student_id)
    )
    """)
else:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        student_id TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        marked_by TEXT DEFAULT 'qr',
        UNIQUE(session_id, student_id),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
    """)

# ---------------------------
# SCHEDULES TABLE
# ---------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,
    subject TEXT NOT NULL,
    class_name TEXT NOT NULL,
    section TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    FOREIGN KEY (teacher_id) REFERENCES users(id)
)
""")

# ---------------------------
# ANNOUNCEMENTS TABLE
# ---------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT NOT NULL,
    priority TEXT DEFAULT 'normal',
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
)
""")

# ---------------------------
# DEFAULT ADMIN USER
# ---------------------------
if USE_POSTGRES:
    cursor.execute(
        """
        INSERT INTO users (username, password_hash, role)
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO NOTHING
        """,
        ("admin", hash_password("admin123"), "admin")
    )
else:
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (username, password_hash, role)
        VALUES (?, ?, ?)
        """,
        ("admin", hash_password("admin123"), "admin")
    )

conn.commit()
