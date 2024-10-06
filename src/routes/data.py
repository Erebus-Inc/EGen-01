from fastapi import APIRouter,FastAPI,Depends,UploadFile,status
from fastapi.responses import JSONResponse
from helpers import get_settings,Settings
from controllers import dataController,projectController
####

data_route = APIRouter()

@data_route.post("/upload/{project_id}")
async def upload(project_id: str,file : UploadFile , app_settings : Settings = Depends(get_settings)):
    #file validation (size and properties)
    validation , resultSignal = dataController().FILE_VALIDATOR(file = file)
    
    if not validation:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": resultSignal
            }
        )
    
    projectPath = projectController().getProjectPath(project_id=project_id)