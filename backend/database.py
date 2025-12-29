"""
MongoDB database configuration and collections setup
"""
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import ConnectionFailure, OperationFailure
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "attendance_system")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client[DB_NAME]
    logger.info("✅ Connected to MongoDB")
except ConnectionFailure as e:
    logger.error(f"❌ MongoDB connection failed: {e}")
    db = None


def init_db():
    """Initialize database collections and indexes"""
    if db is None:
        logger.error("Database not initialized")
        return

    try:
        # Create collections if they don't exist
        collections = [
            "platform_admins",
            "organizations",
            "organization_settings",
            "users",
            "students",
            "faculty",
            "subjects",
            "courses",
            "batches",
            "rooms",
            "timetables",
            "attendance_sessions",
            "attendance_entries",
            "attendance_rules",
            "notifications",
            "audit_logs",
            "exports",
            "login_history",
        ]

        for collection_name in collections:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                logger.info(f"✅ Created collection: {collection_name}")

        # Create indexes for performance
        create_indexes()
        logger.info("✅ All indexes created")

    except OperationFailure as e:
        logger.error(f"❌ Database initialization error: {e}")


def create_indexes():
    """Create database indexes for optimized queries"""

    # Users collection
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.users.create_index([("organization_id", ASCENDING)])
    db.users.create_index([("role", ASCENDING)])
    db.users.create_index([("created_at", DESCENDING)])

    # Students collection
    db.students.create_index([("organization_id", ASCENDING)])
    db.students.create_index([("roll_number", ASCENDING)])
    db.students.create_index([("batch", ASCENDING)])
    db.students.create_index([("email", ASCENDING), ("organization_id", ASCENDING)], unique=True)

    # Faculty collection
    db.faculty.create_index([("organization_id", ASCENDING)])
    db.faculty.create_index([("employee_id", ASCENDING)])
    db.faculty.create_index([("department", ASCENDING)])

    # Subjects collection
    db.subjects.create_index([("organization_id", ASCENDING)])
    db.subjects.create_index([("code", ASCENDING)])
    db.subjects.create_index([("department", ASCENDING)])

    # Batches collection
    db.batches.create_index([("organization_id", ASCENDING)])
    db.batches.create_index([("semester", ASCENDING)])

    # Timetables collection
    db.timetables.create_index([("organization_id", ASCENDING)])
    db.timetables.create_index([("faculty_id", ASCENDING)])
    db.timetables.create_index([("batch_id", ASCENDING)])
    db.timetables.create_index([("room_id", ASCENDING)])

    # Attendance sessions
    db.attendance_sessions.create_index([("organization_id", ASCENDING)])
    db.attendance_sessions.create_index([("faculty_id", ASCENDING)])
    db.attendance_sessions.create_index([("batch_id", ASCENDING)])
    db.attendance_sessions.create_index([("date", DESCENDING)])
    db.attendance_sessions.create_index([("status", ASCENDING)])

    # Attendance entries
    db.attendance_entries.create_index([("organization_id", ASCENDING)])
    db.attendance_entries.create_index([("session_id", ASCENDING)])
    db.attendance_entries.create_index([("student_id", ASCENDING)])
    db.attendance_entries.create_index([("session_id", ASCENDING), ("student_id", ASCENDING)], unique=True)

    # Notifications
    db.notifications.create_index([("organization_id", ASCENDING)])
    db.notifications.create_index([("user_id", ASCENDING)])
    db.notifications.create_index([("created_at", DESCENDING)])
    db.notifications.create_index([("read_at", ASCENDING)])

    # Audit logs
    db.audit_logs.create_index([("organization_id", ASCENDING)])
    db.audit_logs.create_index([("user_id", ASCENDING)])
    db.audit_logs.create_index([("created_at", DESCENDING)])
    db.audit_logs.create_index([("action", ASCENDING)])

    # Login history
    db.login_history.create_index([("user_id", ASCENDING)])
    db.login_history.create_index([("created_at", DESCENDING)])

    # Exports
    db.exports.create_index([("organization_id", ASCENDING)])
    db.exports.create_index([("created_at", DESCENDING)])

    # Organizations
    db.organizations.create_index([("code", ASCENDING)], unique=True)


# Helper function to convert ObjectId to string
def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return None
    doc["_id"] = str(doc["_id"])
    return doc


def serialize_docs(docs):
    """Convert list of MongoDB documents to JSON-serializable format"""
    return [serialize_doc(doc) for doc in docs]
