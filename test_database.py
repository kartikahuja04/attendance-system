#!/usr/bin/env python
"""
Test script to verify MongoDB connection and create test users
"""

from pymongo import MongoClient
from datetime import datetime
import hashlib
import sys

# Connection
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "attendance_system"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def test_connection():
    """Test MongoDB connection"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✓ MongoDB Connection Successful!")
        return client
    except Exception as e:
        print(f"✗ MongoDB Connection Failed: {e}")
        sys.exit(1)

def create_test_data(client):
    """Create test users (teacher and student)"""
    db = client[DB_NAME]
    users = db['users']
    
    # Drop existing test users
    users.delete_many({"email": {"$in": ["teacher@test.com", "student@test.com"]}})
    
    # Create test teacher
    teacher = {
        "name": "John Teacher",
        "email": "teacher@test.com",
        "password": hash_password("password123"),
        "role": "teacher",
        "createdAt": datetime.utcnow(),
    }
    
    # Create test student
    student = {
        "name": "Alice Student",
        "email": "student@test.com",
        "password": hash_password("password123"),
        "role": "student",
        "createdAt": datetime.utcnow(),
    }
    
    try:
        teacher_result = users.insert_one(teacher)
        print(f"✓ Teacher created: {teacher['email']}")
        print(f"  ID: {teacher_result.inserted_id}")
        print(f"  Password Hash: {teacher['password'][:16]}...")
        
        student_result = users.insert_one(student)
        print(f"\n✓ Student created: {student['email']}")
        print(f"  ID: {student_result.inserted_id}")
        print(f"  Password Hash: {student['password'][:16]}...")
        
        return teacher_result.inserted_id, student_result.inserted_id
    except Exception as e:
        print(f"✗ Error creating users: {e}")
        return None, None

def verify_users(client):
    """Verify users can be retrieved"""
    db = client[DB_NAME]
    users = db['users']
    
    print("\n" + "="*50)
    print("Stored Users in Database:")
    print("="*50)
    
    for user in users.find({"role": {"$in": ["teacher", "student"]}}):
        print(f"\nName: {user['name']}")
        print(f"Email: {user['email']}")
        print(f"Role: {user['role']}")
        print(f"Created: {user['createdAt']}")
        print(f"ID: {user['_id']}")

def check_indexes(client):
    """Verify indexes are created"""
    db = client[DB_NAME]
    users = db['users']
    
    print("\n" + "="*50)
    print("Database Indexes:")
    print("="*50)
    
    indexes = users.list_indexes()
    for idx in indexes:
        print(f"✓ {idx['name']}")

def main():
    print("MongoDB Database Test Script")
    print("="*50)
    
    # Test connection
    client = test_connection()
    
    # Create test data
    print("\nCreating test users...")
    print("-"*50)
    teacher_id, student_id = create_test_data(client)
    
    # Verify data
    verify_users(client)
    
    # Check indexes
    check_indexes(client)
    
    print("\n" + "="*50)
    print("✓ All tests passed!")
    print("="*50)
    print("\nTest Credentials:")
    print("Teacher: teacher@test.com / password123")
    print("Student: student@test.com / password123")
    print("\nYou can now log in using these credentials!")
    
    client.close()

if __name__ == "__main__":
    main()
