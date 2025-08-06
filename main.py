from fastapi import FastAPI
from routes import webapp
import sys
import os

sys.path.append(os.path.dirname(__file__))

app = FastAPI()

app.include_router(webapp.router, prefix="/api")
