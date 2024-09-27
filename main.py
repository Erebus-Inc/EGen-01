from fastapi import *
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(
    title="EGen-01",
    description="",
    version="0.1",
    docs_url=None,
    redoc_url=None
)

