"""
Main FastAPI application for Attendance Management System
Enterprise-grade, production-ready
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import routes
from backend.routes_auth_v2 import router as auth_router
from backend.routes_organization import router as org_router
from backend.routes_students import router as students_router
from backend.routes_faculty import router as faculty_router
from backend.routes_batches_rooms import router as batches_rooms_router
from backend.routes_timetable import router as timetable_router
from backend.routes_attendance_v2 import router as attendance_router
from backend.routes_reports import router as reports_router
from backend.routes_notifications import router as notifications_router
from backend.database import init_db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="University Attendance Management System",
    description="Enterprise-grade attendance management system for universities and institutes",
    version="2.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Add CORS middleware
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

if os.getenv("VERCEL"):
    allowed_origins.extend([
        "https://attendance-system-frontend.vercel.app",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app", "*.herokuapp.com"],
)

# Initialize database
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Attendance Management System...")
    init_db()
    logger.info("✅ Database initialized")


# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(org_router, prefix="/api/organizations", tags=["Organizations"])
app.include_router(students_router, prefix="/api/students", tags=["Students"])
app.include_router(faculty_router, prefix="/api/faculty", tags=["Faculty"])
app.include_router(batches_rooms_router, prefix="/api", tags=["Batches & Rooms"])
app.include_router(timetable_router, prefix="/api/timetables", tags=["Timetables"])
app.include_router(attendance_router, prefix="/api/attendance", tags=["Attendance"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports & Exports"])
app.include_router(notifications_router, prefix="/api", tags=["Notifications & Audit"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Attendance Management System API",
        "version": "2.0.0",
        "docs": "/api/docs",
    }
