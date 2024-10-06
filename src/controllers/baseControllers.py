from helpers.config import get_settings,Settings
import os
import random
import string
class baseController:
    def __init__(self):
        self.app_settings = get_settings()
        self.baseDire = os.path.dirname(os.path.dirname(__file__))
       #self.fileDire = self.baseDire + "/" + "assets/files"
        self.fileDire = os.path.join(
            self.baseDire,"assets/files"
        )
        
    def random_string(self,length:int = 12):
        return ''.join(random.choices(string.ascii_lowercase + string.digits , k = length))