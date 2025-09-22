from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from routes import webapp
from contextlib import asynccontextmanager
from starlette.routing import Route, WebSocketRoute, Mount
from pathlib import Path
import sys, os, uvicorn

sys.path.append(os.path.dirname(__file__))

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ Зарегистрированные маршруты:")
    for r in app.router.routes:
        if isinstance(r, Route):
            print(f"{r.path} — {r.methods}")
        elif isinstance(r, WebSocketRoute):
            print(f"{r.path} — WEBSOCKET")
        elif isinstance(r, Mount):
            print(f"{r.path} — MOUNT {getattr(r.app, '__class__', type(r.app)).__name__}")
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(webapp.router, prefix="/api")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


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
