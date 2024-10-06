from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Define app settings here.
    APP_NAME:str 
    APP_VERSION:str
    OPEN_AI_API:str
    # Define files settings here.
    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int
    class Config:
        env_file = ".env"
        
def get_settings():
    return Settings()