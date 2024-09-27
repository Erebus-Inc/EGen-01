from fastapi import APIRouter,FastAPI
from os import getenv

base_route = APIRouter()

@base_route.get('/')
async def home():
    app_name = getenv('APP_NAME')
    app_version = getenv('APP_VERSION')
    return {
        "App Name": app_name,
        "App Version": app_version
        }
