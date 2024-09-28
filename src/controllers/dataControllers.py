from .baseControllers import baseController
from fastapi import UploadFile

class dataController(baseController):
    def __init__(self):
        super().__init__()
        self.size_scale = 1048576
    def FILE_VALIDATOR(self,file:UploadFile):
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False , 
        
        if file.size > self.app_settings.FILE_MAX_SIZE*self.size_scale:
            return False , 
        
        return True , 