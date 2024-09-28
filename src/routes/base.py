from fastapi import APIRouter,FastAPI,Depends
from helpers import get_settings,Settings
####
base_route = APIRouter(
    tags=["Home"]
)
####
@base_route.get('/')
async def home(app_settings : Settings = Depends(get_settings)):
    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION
    return {
        "App Name": app_name,
        "App Version": app_version
        }
