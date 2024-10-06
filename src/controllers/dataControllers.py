from .baseControllers import baseController
from .projectControllers import projectController
from fastapi import UploadFile
from Models import responseSignals
import re
import os
class dataController(baseController):
    def __init__(self):
        super().__init__()
        self.size_scale = 1048576
    def FILE_VALIDATOR(self,file:UploadFile):
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False , responseSignals.FILE_TYPE_NOT_SUPPORTED.value
        
        if file.size > self.app_settings.FILE_MAX_SIZE*self.size_scale:
            return False , responseSignals.FILE_SIZE_EXCEEDED.value
        
        return True , responseSignals.FILE_VALIDATED_SUCCESS.value
    
    def name_Generate(self,org:str,project_id:str):
        randomKey = self.random_string()
        projectPath = projectController().getProjectPath(project_id=project_id)
        new_file_Name = self.clean_file_name(org = org) 
        new_file_path = os.path.join(projectPath,randomKey+"_"+new_file_Name)
        
        while os.path.exists(new_file_path):
            randomKey = self.random_string()
            new_file_path = os.path.join(projectPath,randomKey+"_"+new_file_Name)
            
        return new_file_path
        
    def clean_file_name(self,org:str):
        new_file_Name = re.sub(r'[^\w.]','',org.strip())
        
        new_file_Name =  new_file_Name.replace("","_")
        
        return new_file_Name
    