from fastapi import FastAPI
from routes import webapp

app = FastAPI()

app.include_router(webapp.router, prefix="/api")
