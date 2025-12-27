from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, constr
from pymongo.errors import DuplicateKeyError
from bson import ObjectId

try:
    from backend.mongo import get_collection
    from backend.auth import hash_password, verify_password, create_access_token, get_current_user
except Exception:
    from .mongo import get_collection
    from .auth import hash_password, verify_password, create_access_token, get_current_user


router = APIRouter()

# In-memory fallback store for development when MongoDB is unavailable
USERS_MEMORY = {}

@router.get('/ping')
async def ping():
    users = get_collection('users')
    return { 'ok': True, 'usersNone': users is None }


class SignupBody(BaseModel):
    name: constr(min_length=2, max_length=100)
    email: EmailStr
    password: constr(min_length=8)
    role: str  # admin | teacher | student


class LoginBody(BaseModel):
    email: EmailStr
    password: constr(min_length=8)


@router.post('/signup')
async def signup(body: SignupBody):
    users = get_collection('users')
    if users is None:
        # Dev fallback: store users in memory when DB is unavailable
        email = body.email.lower()
        if email in USERS_MEMORY:
            raise HTTPException(status_code=409, detail='Email already registered')
        _id = ObjectId()
        doc = {
            '_id': _id,
            'name': body.name,
            'email': email,
            'password': hash_password(body.password),
            'role': body.role if body.role in ['admin', 'teacher', 'student'] else 'student',
            'createdAt': datetime.utcnow(),
        }
        try:
            print('[DEBUG] signup memory fallback', doc)
        except Exception:
            pass
        USERS_MEMORY[email] = doc
        return {
            'id': str(_id),
            'name': doc['name'],
            'email': doc['email'],
            'role': doc['role'],
            'createdAt': doc['createdAt'].isoformat() + 'Z'
        }
    doc = {
        'name': body.name,
        'email': body.email.lower(),
        'password': hash_password(body.password),
        'role': body.role if body.role in ['admin', 'teacher', 'student'] else 'student',
        'createdAt': datetime.utcnow(),
    }
    try:
        res = users.insert_one(doc)
        return {
            'id': str(res.inserted_id),
            'name': doc['name'],
            'email': doc['email'],
            'role': doc['role'],
            'createdAt': doc['createdAt'].isoformat() + 'Z'
        }
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail='Email already registered')


@router.post('/login')
async def login(body: LoginBody):
    users = get_collection('users')
    if users is None:
        # Dev fallback: authenticate against in-memory store
        email = body.email.lower()
        doc = USERS_MEMORY.get(email)
    else:
        doc = users.find_one({'email': body.email.lower()})
    if not doc:
        raise HTTPException(status_code=401, detail='Invalid credentials')
    if not verify_password(body.password, doc['password']):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    token = create_access_token(
        str(doc['_id']),
        doc.get('role', 'student'),
        { 'name': doc.get('name'), 'email': doc.get('email') }
    )
    return {
        'token': token,
        'user': {
            'id': str(doc['_id']),
            'name': doc.get('name'),
            'email': doc.get('email'),
            'role': doc.get('role', 'student'),
        }
    }


@router.get('/me')
async def me(user = Depends(get_current_user)):
    return { 'user': user }