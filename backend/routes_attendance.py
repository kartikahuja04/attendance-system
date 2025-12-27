from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from bson import ObjectId
import io
import openpyxl
from openpyxl.styles import Font, Alignment

try:
    from backend.mongo import get_collection
except Exception:
    from .mongo import get_collection


router = APIRouter()


@router.get('/attendance/{session_id}')
async def get_attendance(session_id: str):
    attendance = get_collection('attendance')
    sessions = get_collection('sessions')
    if attendance is None or sessions is None:
        raise HTTPException(status_code=500, detail='Database not available')

    sess = sessions.find_one({'sessionId': session_id})
    if not sess:
        raise HTTPException(status_code=404, detail='Session not found')

    docs = list(attendance.find({'sessionId': session_id}).sort('timestamp', 1))
    return {
        'session': {
            'session_id': session_id,
            'subject': sess.get('subject'),
            'class_name': sess.get('class_name'),
            'section': sess.get('section'),
            'date': sess.get('date'),
            'status': sess.get('status', 'active'),
        },
        'attendance': [
            {
                'id': str(d['_id']),
                'student_id': d.get('studentId'),
                'timestamp': d.get('timestamp'),
                'marked_by': d.get('marked_by', 'manual')
            } for d in docs
        ]
    }


@router.get('/attendance/view/{session_id}')
async def view_attendance(session_id: str):
    attendance = get_collection('attendance')
    sessions = get_collection('sessions')
    if attendance is None or sessions is None:
        raise HTTPException(status_code=500, detail='Database not available')
    sess = sessions.find_one({'sessionId': session_id})
    if not sess:
        raise HTTPException(status_code=404, detail='Session not found')
    docs = list(attendance.find({'sessionId': session_id}).sort('timestamp', 1))
    present = len(docs)
    # Absent count would require roster; return present only
    return {
        'session': {
            'subject': sess.get('subject'),
            'class_name': sess.get('class_name'),
            'section': sess.get('section'),
            'date': sess.get('date'),
        },
        'present_students': present,
        'students': [
            {
                'student_id': d.get('studentId'),
                'timestamp': d.get('timestamp')
            } for d in docs
        ]
    }


@router.get('/attendance/export/{session_id}')
async def export_attendance(session_id: str):
    attendance = get_collection('attendance')
    sessions = get_collection('sessions')
    if attendance is None or sessions is None:
        raise HTTPException(status_code=500, detail='Database not available')
    sess = sessions.find_one({'sessionId': session_id})
    if not sess:
        raise HTTPException(status_code=404, detail='Session not found')
    docs = list(attendance.find({'sessionId': session_id}).sort('timestamp', 1))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Attendance'

    ws.append(['Subject', sess.get('subject', '')])
    ws.append(['Class', f"{sess.get('class_name', '')} - {sess.get('section', '')}"])
    ws.append(['Date', sess.get('date', '')])
    ws.append([])
    ws.append(['Student ID', 'Timestamp'])
    for cell in ws[5]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    for d in docs:
        ws.append([d.get('studentId', ''), d.get('timestamp', '')])

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    filename = f"attendance_{session_id}.xlsx"
    return StreamingResponse(stream, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={
        'Content-Disposition': f'attachment; filename="{filename}"'
    })