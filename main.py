from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
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

app = FastAPI(lifespan=lifespan)

app.include_router(webapp.router, prefix="/api")

app.mount("/", StaticFiles(directory="static", html=True), name="static")


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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
