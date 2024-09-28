from fastapi import APIRouter,FastAPI,Depends,UploadFile
from helpers import get_settings,Settings
from controllers import dataController
####

data_route = APIRouter()

@data_route.post("/upload/{project_id}")
async def upload(project_id: str,file : UploadFile , app_settings : Settings = Depends(get_settings)):
    #file validation (size and properties)
    validation , resultSignal = dataController().FILE_VALIDATOR(file = file)
    
    return{
        "signal": resultSignal
    }