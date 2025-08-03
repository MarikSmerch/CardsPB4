from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import Base
from . import models
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)


def create_all_tables():
    Base.metadata.create_all(bind=engine)
