from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Define your settings here.
    APP_NAME:str 
    APP_VERSION:str
    OPEN_AI_API:str
    
    class Config:
        env_file = ".env"
        
def get_settings():
    return Settings()