from fastapi import APIRouter,FastAPI,Depends,UploadFile,status
from fastapi.responses import JSONResponse
from helpers import get_settings,Settings
from controllers import dataController,projectController
from Models import responseSignals
from .schemes.data import processRequest
import os
import aiofiles
import logging
####

logger = logging.getLogger('uvicorn.errors')

data_route = APIRouter()
data_Controller = dataController()
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
    
    projectDir = projectController().getProjectPath(project_id=project_id)
    filePath , fileID = data_Controller.path_Generate(org = file.filename,project_id=project_id)
    try:
        async with aiofiles.open(filePath,"wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error("Error while uploading file: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": responseSignals.FILE_UPLOAD_FAILED.value
            }
        )
            
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": responseSignals.FILE_UPLOAD_SUCCESSFULLY.value,
            "file ID": fileID
        }
    )

