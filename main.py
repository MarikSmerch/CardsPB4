from fastapi import FastAPI
from routes import webapp
from contextlib import asynccontextmanager
import sys
import os
import uvicorn

sys.path.append(os.path.dirname(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ Зарегистрированные маршруты:")
    for route in app.routes:
        print(f"{route.path} — {route.methods}")
    yield

app = FastAPI()

app.include_router(webapp.router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)