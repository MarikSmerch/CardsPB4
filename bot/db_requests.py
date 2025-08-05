from db import SessionLocal
from db.models import User
from sqlalchemy.orm import Session
from datetime import datetime
from telebot.util import check_webapp_signature, parse_webapp_init_data

import os

BOT_TOKEN = os.getenv("TOKEN")


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


def get_or_create_user_by_telegram_init_data(db: Session, init_data: str):
    try:
        data = parse_webapp_init_data(init_data)
    except Exception as e:
        raise ValueError("Ошибка разбора initData") from e

    if not check_webapp_signature(BOT_TOKEN, init_data):
        raise ValueError("Неверная подпись initData")

    tg_user = data.get("user")
    if not tg_user:
        raise ValueError("Пользователь не найден в initData")

    telegram_id = tg_user["id"]
    username = tg_user.get("username")
    first_name = tg_user.get("first_name")
    last_name = tg_user.get("last_name")
    avatar_url = None  # можно добавить позже через бота

    user = db.query(User).filter_by(id=telegram_id).first()
    if user:
        return user

    user = User(
        id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        avatar_url=avatar_url,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
