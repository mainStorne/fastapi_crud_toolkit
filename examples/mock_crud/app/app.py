from fastapi import FastAPI, Request
from .api import api
from fastapi_pagination import add_pagination


app = FastAPI()
app.include_router(api)
add_pagination(app)