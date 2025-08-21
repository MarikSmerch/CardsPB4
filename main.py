from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from routes import webapp
from contextlib import asynccontextmanager
from pathlib import Path
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

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(lifespan=lifespan)
app.include_router(webapp.router, prefix="/api")
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


@app.middleware("http")
async def cache_headers(request: Request, call_next):
    response: Response = await call_next(request)
    p = request.url.path
    if p.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")):
        response.headers["Cache-Control"] = "public, immutable, max-age=31536000"
    elif p.endswith((".css", ".js")):
        response.headers["Cache-Control"] = "public, immutable, max-age=31536000"
    elif p.endswith(".html"):
        response.headers["Cache-Control"] = "no-cache"
    return response

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
