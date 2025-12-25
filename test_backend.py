from backend.main import app
import uvicorn

if __name__ == "__main__":
    print("Testing backend startup...")
    try:
        # Just try to access something that might trigger db connection
        from backend.db import cursor
        cursor.execute("SELECT 1")
        print("Database connectivity OK")
        print("Backend main.app initialized OK")
    except Exception as e:
        print(f"ERROR: {e}")
