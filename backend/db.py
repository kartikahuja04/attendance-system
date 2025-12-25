import sqlite3
import hashlib
import os
import re

USE_POSTGRES = bool(os.getenv("DATABASE_URL"))
DB_INIT_ERROR = None

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import DictCursor

    class PlaceholderCursor:
        """Wrap a psycopg2 cursor so that code using '?' placeholders continues to work.
        It converts '?' to '%s' and passes through to psycopg2.
        """
        def __init__(self, real_cursor):
            self._cur = real_cursor

        def execute(self, query, params=None):
            if params is None:
                return self._cur.execute(query)
            q = query.replace("?", "%s")
            return self._cur.execute(q, params)

        def executemany(self, query, seq_of_params):
            q = query.replace("?", "%s")
            return self._cur.executemany(q, seq_of_params)

        def fetchone(self):
            return self._cur.fetchone()

        def fetchall(self):
            return self._cur.fetchall()

    class FailingCursor:
        def __init__(self, error_msg: str):
            self._err = error_msg
        def execute(self, *args, **kwargs):
            raise RuntimeError(f"Database not initialized: {self._err}")
        def executemany(self, *args, **kwargs):
            raise RuntimeError(f"Database not initialized: {self._err}")
        def fetchone(self):
            raise RuntimeError(f"Database not initialized: {self._err}")
        def fetchall(self):
            raise RuntimeError(f"Database not initialized: {self._err}")

    try:
        dsn = os.getenv("DATABASE_URL")
        # Ensure sslmode=require if not present (common for managed providers)
        if "sslmode=" not in dsn:
            if "?" in dsn:
                dsn = f"{dsn}&sslmode=require"
            else:
                dsn = f"{dsn}?sslmode=require"

        _conn = psycopg2.connect(dsn, cursor_factory=DictCursor)
        _conn.autocommit = True
        _cursor = _conn.cursor()
        cursor = PlaceholderCursor(_cursor)
        conn = _conn

        # Initialize schema for Postgres
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS teachers (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                session_id TEXT UNIQUE NOT NULL,
                teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
                class_name TEXT NOT NULL,
                subject TEXT NOT NULL,
                section TEXT NOT NULL,
                start_time TIMESTAMPTZ NOT NULL,
                end_time TIMESTAMPTZ,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                student_id TEXT NOT NULL,
                timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                marked_by TEXT DEFAULT 'qr'
            )
            """
        )
        # Unique index to prevent duplicates
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_session_student
            ON attendance(session_id, student_id)
            """
        )

        # Default admin
        default_password_hash = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute(
            """
            INSERT INTO teachers (username, password_hash)
            VALUES ('admin', ?)
            ON CONFLICT (username) DO NOTHING
            """,
            (default_password_hash,),
        )
    except Exception as e:
        DB_INIT_ERROR = str(e)
        conn = None
        cursor = FailingCursor(DB_INIT_ERROR)
else:
    # SQLite Database (local file or serverless tmp)
    db_path = os.getenv("DB_PATH") if os.getenv("DB_PATH") else ("/tmp/attendance.db" if os.getenv("VERCEL") else "attendance.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    # Enforce FKs and improve concurrency
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass

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
    # Unique constraint to prevent duplicate marks
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_session_student ON attendance(session_id, student_id)")
    except Exception:
        pass

    # Create schedules table for teacher class schedules
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER NOT NULL,
        day_of_week TEXT NOT NULL,
        subject TEXT NOT NULL,
        subject_code TEXT,
        class_name TEXT NOT NULL,
        section TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        room TEXT,
        FOREIGN KEY (teacher_id) REFERENCES teachers(id)
    )
    """)

    # Create announcements table for dashboard
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT NOT NULL,
        priority TEXT DEFAULT 'normal',
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME,
        FOREIGN KEY (created_by) REFERENCES teachers(id)
    )
    """)

    # Create class_rosters table for student lists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS class_rosters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT NOT NULL,
        section TEXT NOT NULL,
        student_id TEXT NOT NULL,
        student_name TEXT,
        UNIQUE(class_name, section, student_id)
    )
    """)

    # Migration: ensure 'marked_by' column exists on 'attendance'
    try:
        cursor.execute("PRAGMA table_info(attendance)")
        cols = [row[1] for row in cursor.fetchall()]
        if 'marked_by' not in cols:
            cursor.execute("ALTER TABLE attendance ADD COLUMN marked_by TEXT DEFAULT 'qr'")
    except Exception:
        pass

    # Migration: Add profile fields to teachers table
    try:
        cursor.execute("PRAGMA table_info(teachers)")
        existing_cols = [row[1] for row in cursor.fetchall()]
        
        # Define new profile columns
        profile_columns = {
            'employee_id': 'TEXT',
            'full_name': 'TEXT',
            'email': 'TEXT',
            'phone': 'TEXT',
            'department': 'TEXT',
            'designation': 'TEXT',
            'qualification': 'TEXT',
            'education': 'TEXT',
            'subjects_taught': 'TEXT',
            'research_areas': 'TEXT',
            'publications': 'TEXT',
            'bio': 'TEXT',
            'profile_picture_url': 'TEXT',
            'resume_url': 'TEXT',
            'linkedin_url': 'TEXT',
            'google_scholar_url': 'TEXT',
            'profile_visible': 'INTEGER DEFAULT 1'  # 1 = visible, 0 = hidden
        }
        
        # Add missing columns
        for col_name, col_type in profile_columns.items():
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE teachers ADD COLUMN {col_name} {col_type}")
    except Exception as e:
        print(f"Profile migration warning: {e}")

    # Default admin
    default_password_hash = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute(
        """
        INSERT OR IGNORE INTO teachers (username, password_hash)
        VALUES ('admin', ?)
        """,
        (default_password_hash,),
    )

    conn.commit()
