import os
from typing import Optional

from pymongo import MongoClient, ASCENDING, errors
from dotenv import load_dotenv


# Load environment from project root or current directory
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
load_dotenv()  # fallback


MONGO_DB_NAME: str = os.getenv('MONGO_DB_NAME', 'attendance_system')

client: Optional[MongoClient] = None
db = None
MONGO_INIT_ERROR: Optional[str] = None


def connect_mongo():
    """Connect to MongoDB using env MONGO_URI and set globals.
    Falls back to an in-memory mongomock client when unavailable or disabled for local dev.
    """
    global client, db, MONGO_INIT_ERROR

    # Read env dynamically to allow runtime changes
    mongo_uri: Optional[str] = os.getenv('MONGO_URI')
    use_mock: bool = os.getenv('USE_MOCK_MONGO', 'false').lower() in ('1', 'true', 'yes')

    # Explicit mock mode for local development
    if use_mock:
        try:
            import mongomock as _mongomock
            client = _mongomock.MongoClient()
            db = client[MONGO_DB_NAME]
            MONGO_INIT_ERROR = None
            return db
        except Exception as e:
            # Continue to real Mongo attempt if mongomock import failed
            MONGO_INIT_ERROR = f"mongomock_import_failed: {e}"
            client = None
            db = None
            # fall through

    # Try real Mongo if URI is provided
    if mongo_uri:
        try:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')  # verify connection
            db = client[MONGO_DB_NAME]
            MONGO_INIT_ERROR = None
            return db
        except errors.PyMongoError as e:
            # Fall back to mongomock if available
            try:
                import mongomock as _mongomock
                client = _mongomock.MongoClient()
                db = client[MONGO_DB_NAME]
                MONGO_INIT_ERROR = None
                return db
            except Exception:
                pass
            MONGO_INIT_ERROR = str(e)
            client = None
            db = None
            return None

    # No URI provided: attempt mongomock fallback
    try:
        import mongomock as _mongomock
        client = _mongomock.MongoClient()
        db = client[MONGO_DB_NAME]
        MONGO_INIT_ERROR = None
        return db
    except Exception:
        MONGO_INIT_ERROR = 'Missing MONGO_URI environment variable and mongomock not installed'
        return None


def get_db():
    """Get the connected database, attempting connection if needed."""
    global db
    if db is not None:
        return db
    return connect_mongo()


def get_collection(name: str):
    database = get_db()
    if not database:
        return None
    return database[name]


def init_indexes():
    """Create required indexes for production usage."""
    database = get_db()
    if not database:
        return False
    try:
        users = database['users']
        sessions = database['sessions']
        attendance = database['attendance']

        # Unique email for users
        users.create_index([('email', ASCENDING)], unique=True, name='uniq_email')
        users.create_index([('role', ASCENDING)], name='role_idx')
        users.create_index([('createdAt', ASCENDING)], name='createdAt_idx')

        # Sessions indexes
        sessions.create_index([('teacherId', ASCENDING), ('date', ASCENDING)], name='teacher_date_idx')
        sessions.create_index([('subject', ASCENDING)], name='subject_idx')

        # Attendance indexes
        attendance.create_index([('sessionId', ASCENDING), ('studentId', ASCENDING)], unique=True, name='uniq_session_student')
        attendance.create_index([('timestamp', ASCENDING)], name='timestamp_idx')
        return True
    except errors.PyMongoError:
        return False