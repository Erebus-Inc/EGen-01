from .baseControllers import baseController
from fastapi import UploadFile
from Models import responseSignals
import os

class projectController(baseController):
    
    def __init__(self):
        super().__init__()
    
    def getProjectPath(self,project_id:str):
        projectDir = os.join(
            self.fileDire,
            project_id
        )
        
        if not os.path.exists(projectDir):
            os.makedirs(projectDir)
        
        return projectDir