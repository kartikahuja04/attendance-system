from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes_auth import router as auth_router
from routes_attendance import router as attendance_router

app = FastAPI(
    title="Attendance Management System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite frontend
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])
