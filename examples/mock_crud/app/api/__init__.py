from fastapi import APIRouter
from .endpoints import users

api = APIRouter()
api.include_router(users.r, prefix='/users', tags=['users'])
