from pymongo import MongoClient

MONGO_URL = "mongodb://localhost:27017"

client = MongoClient(MONGO_URL)

db = client["attendance_system"]

attendance_collection = db["attendance"]
users_collection = db["users"]
sessions_collection = db["sessions"]