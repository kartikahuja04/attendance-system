from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Form, Request, Cookie, Header
from pydantic import BaseModel, constr
import uuid

try:
    from backend.mongo import get_collection
    from backend.auth import get_current_user, require_roles
except Exception:
    from .mongo import get_collection
    from .auth import get_current_user, require_roles


router = APIRouter()


class CreateSessionBody(BaseModel):
    class_name: constr(min_length=1, max_length=100)
    subject: constr(min_length=1, max_length=100)
    section: constr(min_length=1, max_length=50)
    start_time: constr(min_length=10, max_length=30)  # ISO datetime string


def _iso_date(dt_str: str) -> str:
    try:
        # Expecting 'YYYY-MM-DDTHH:mm'
        dt = datetime.fromisoformat(dt_str)
        return dt.date().isoformat()
    except Exception:
        # Fallback: try to parse only date part
        return dt_str[:10]


@router.get('/sessions')
async def list_sessions(date: Optional[str] = None):
    sessions = get_collection('sessions')
    if sessions is None:
        raise HTTPException(status_code=500, detail='Database not available')
    q = {}
    if date:
        q['date'] = date
    docs = list(sessions.find(q).sort('start_time', 1))
    return {
        'sessions': [
            {
                'id': str(d['_id']),
                'session_id': d.get('sessionId'),
                'subject': d.get('subject'),
                'class_name': d.get('class_name'),
                'section': d.get('section'),
                'date': d.get('date'),
                'status': d.get('status', 'active')
            } for d in docs
        ]
    }


@router.get('/sessions/active')
async def list_active_sessions():
    sessions = get_collection('sessions')
    if sessions is None:
        raise HTTPException(status_code=500, detail='Database not available')
    docs = list(sessions.find({'status': 'active'}).sort('start_time', 1))
    return {
        'sessions': [
            {
                'id': str(d['_id']),
                'session_id': d.get('sessionId'),
                'subject': d.get('subject'),
                'class_name': d.get('class_name'),
                'section': d.get('section'),
                'date': d.get('date'),
                'status': 'active'
            } for d in docs
        ]
    }


@router.post('/sessions/create')
async def create_session(
    request: Request,
    user = Depends(get_current_user),
    class_name: str = Form(...),
    subject: str = Form(...),
    section: str = Form(...),
    start_time: str = Form(...),
    session_token: Optional[str] = Cookie(None),
    x_auth_token: Optional[str] = Header(None, alias='X-Auth-Token')
):
    sessions = get_collection('sessions')
    if sessions is None:
        raise HTTPException(status_code=500, detail='Database not available')

    # Determine teacher identity: prefer JWT user, else legacy header/cookie
    teacher_id = None
    teacher_role = None
    if user:
        teacher_id = user.get('id')
        teacher_role = user.get('role')
    else:
        teacher_id = x_auth_token or session_token
        teacher_role = 'teacher'
    if not teacher_id:
        raise HTTPException(status_code=401, detail='Not authenticated')

    if teacher_role not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail='Forbidden')

    doc = {
        'sessionId': uuid.uuid4().hex,
        'teacherId': teacher_id,
        'class_name': class_name,
        'subject': subject,
        'section': section,
        'start_time': start_time,
        'date': _iso_date(start_time),
        'status': 'active',
        'createdAt': datetime.utcnow(),
    }
    res = sessions.insert_one(doc)
    return {
        'success': True,
        'session_id': doc['sessionId'],
        'id': str(res.inserted_id),
    }


@router.post('/sessions/end')
async def end_session(
    user = Depends(get_current_user),
    session_id: str = Form(...)
):
    sessions = get_collection('sessions')
    if sessions is None:
        raise HTTPException(status_code=500, detail='Database not available')
    if user.get('role') not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail='Forbidden')
    res = sessions.update_one({'sessionId': session_id}, {'$set': {'status': 'ended', 'end_time': datetime.utcnow().isoformat()}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail='Session not found')
    return {'success': True}