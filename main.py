from fastapi import FastAPI
from routes import init

app = FastAPI()

app.include_router(init.router)