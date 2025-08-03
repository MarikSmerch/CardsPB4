from db import SessionLocal
from db.models import User
from datetime import datetime


def add_user(username: str, avatar_url: str | None = None):
    db = SessionLocal()
    existing = db.query(User).filter_by(username=username).first()
    if not existing:
        user = User(
            username=username,
            avatar_url=avatar_url,
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
    db.close()
