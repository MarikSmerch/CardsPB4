from db import SessionLocal
from db.models import User
from datetime import datetime


def add_user(username, avatar_url):
    db = SessionLocal()
    user = db.query(User).filter_by(username=username).first()
    if not user:
        user = User(username=username, avatar_url=avatar_url, created_at=datetime.utcnow())
        db.add(user)
    else:
        user.avatar_url = avatar_url
    db.commit()
    db.close()
