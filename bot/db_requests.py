from bot.db import SessionLocal
from bot.db.models import User
from sqlalchemy.orm import Session
from datetime import datetime
from bot.utils import verify_telegram_init_data
import json

import os

BOT_TOKEN = os.getenv("TOKEN")


def add_user(telegram_id, username, avatar_url):
    db = SessionLocal()
    user = db.query(User).filter_by(id=telegram_id).first()

    if not user:
        user = User(id=telegram_id, username=username, avatar_url=avatar_url, created_at=datetime.utcnow())
        db.add(user)
    else:
        user.avatar_url = avatar_url

    db.commit()
    db.close()
