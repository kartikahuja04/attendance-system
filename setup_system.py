#!/usr/bin/env python3
"""
Setup script for Attendance Management System
Initializes database, creates demo data, and verifies installation
"""

import sys
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are installed"""
    logger.info("Checking dependencies...")
    
    required_packages = [
        'fastapi',
        'pymongo',
        'passlib',
        'python-jose',
        'pydantic',
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.error(f"❌ Missing packages: {', '.join(missing)}")
        logger.info("Run: pip install -r requirements.txt")
        return False
    
    logger.info("✅ All dependencies installed")
    return True

def init_database():
    """Initialize MongoDB collections and indexes"""
    logger.info("Initializing database...")
    
    try:
        from backend.database import init_db, db
        
        if db is None:
            logger.error("❌ MongoDB connection failed")
            return False
        
        init_db()
        logger.info("✅ Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

def create_demo_data():
    """Create demo users for testing"""
    logger.info("Creating demo data...")
    
    try:
        from backend.database import db
        from backend.auth import hash_password
        
        if db is None:
            logger.error("❌ Cannot create demo data - MongoDB not connected")
            return False
        
        # Create demo users
        users_collection = db['users']
        
        demo_users = [
            {
                "email": "admin@university.edu",
                "full_name": "System Administrator",
                "password_hash": hash_password("password123"),
                "role": "super_admin",
                "organization_id": None,
                "is_active": True,
                "created_at": datetime.utcnow(),
            },
            {
                "email": "org_admin@university.edu",
                "full_name": "Organization Administrator",
                "password_hash": hash_password("password123"),
                "role": "org_admin",
                "organization_id": "org_123",
                "is_active": True,
                "created_at": datetime.utcnow(),
            },
            {
                "email": "faculty@university.edu",
                "full_name": "Dr. John Smith",
                "password_hash": hash_password("password123"),
                "role": "faculty",
                "organization_id": "org_123",
                "is_active": True,
                "created_at": datetime.utcnow(),
            },
            {
                "email": "student@university.edu",
                "full_name": "Student User",
                "password_hash": hash_password("password123"),
                "role": "student",
                "organization_id": "org_123",
                "is_active": True,
                "created_at": datetime.utcnow(),
            },
        ]
        
        for user in demo_users:
            if not users_collection.find_one({"email": user["email"]}):
                users_collection.insert_one(user)
                logger.info(f"✅ Created demo user: {user['email']}")
            else:
                logger.info(f"⚠️ Demo user already exists: {user['email']}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create demo data: {e}")
        return False

def verify_installation():
    """Verify the installation by checking all components"""
    logger.info("\n" + "="*50)
    logger.info("VERIFICATION REPORT")
    logger.info("="*50)
    
    checks = [
        ("Dependencies", check_dependencies()),
        ("Database", init_database()),
        ("Demo Data", create_demo_data()),
    ]
    
    all_passed = all(result for _, result in checks)
    
    logger.info("\n" + "-"*50)
    for name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{name}: {status}")
    
    logger.info("-"*50)
    
    if all_passed:
        logger.info("\n✅ Installation verified successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Start backend: uvicorn backend.main:app --reload")
        logger.info("2. Start frontend: cd frontend && npm run dev")
        logger.info("\nDemo Credentials:")
        logger.info("  - Admin: admin@university.edu / password123")
        logger.info("  - Faculty: faculty@university.edu / password123")
        logger.info("  - Student: student@university.edu / password123")
        return 0
    else:
        logger.error("\n❌ Installation verification failed!")
        logger.error("Please fix the issues above and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(verify_installation())
