from fastapi import FastAPI,APIRouter
from dotenv import load_dotenv
from routes import base

load_dotenv()

app = FastAPI(
    title="EGen-01",
    description="",
    version="0.1",
    docs_url=None,
    redoc_url=None
)


app.include_router(base.base_route)