from fastapi import FastAPI
from routes import base,data


app = FastAPI()

app.include_router(base.base_route)
app.include_router(data.data_route)