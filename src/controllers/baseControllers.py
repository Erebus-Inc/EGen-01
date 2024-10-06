from helpers.config import get_settings,Settings
import os

class baseController:
    def __init__(self):
        self.app_settings = get_settings()
        self.baseDire = os.path.dirname(os.path.dirname(__file__))
       #self.fileDire = self.baseDire + "/" + "assets/files"
        self.fileDire = os.path.join(
            self.baseDire,"assets/files"
        )