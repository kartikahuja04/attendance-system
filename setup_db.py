from pymongo import MongoClient
from datetime import datetime
import hashlib

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "attendance_system"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Connect
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
client.admin.command('ping')
print("[SUCCESS] MongoDB Connected Successfully!\n")

db = client[DB_NAME]
users = db['users']

# Delete old test users
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

teacher_result = users.insert_one(teacher)
print(f"[SUCCESS] Teacher created: teacher@test.com")
print(f"  ID: {teacher_result.inserted_id}")

student_result = users.insert_one(student)
print(f"[SUCCESS] Student created: student@test.com")
print(f"  ID: {student_result.inserted_id}")

print("\n" + "="*50)
print("All Users in Database:")
print("="*50)

for user in users.find():
    print(f"\nName: {user['name']}")
    print(f"Email: {user['email']}")
    print(f"Role: {user['role']}")
    print(f"Password Hash: {user['password'][:20]}...")

print("\n" + "="*50)
print("[SUCCESS] Database Setup Complete!")
print("="*50)
print("\nLogin Credentials:")
print("Teacher: teacher@test.com / password123")
print("Student: student@test.com / password123")

client.close()
