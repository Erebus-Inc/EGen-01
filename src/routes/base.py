from fastapi import APIRouter,FastAPI
from helpers.config import get_settings
import os

app_settings = get_settings()

base_route = APIRouter()

@base_route.get('/')
async def home():
    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION
    return {
        "App Name": app_name,
        "App Version": app_version
        }
