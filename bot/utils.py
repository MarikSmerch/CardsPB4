import os
import hmac
import hashlib
import time
import json
from urllib.parse import parse_qsl
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session


from dotenv import load_dotenv, find_dotenv
from bot.db.models import User

load_dotenv(find_dotenv())


def _bot_token() -> str:
    token = os.getenv("TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Server TOKEN is not set")
    return token


INITDATA_TTL_SEC = int(os.getenv("INITDATA_TTL_SEC", "600"))


def verify_telegram_init_data(init_data: str, db: Session) -> User:
    try:
        data = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid initData format")

    received_hash = data.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=400, detail="Missing hash in initData")

    # Формируем data_check_string
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))

    # Проверяем подпись по алгоритму Telegram
    secret_key = hashlib.sha256(_bot_token().encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if computed_hash != received_hash:
        raise HTTPException(status_code=403, detail="Invalid Telegram signature")

    # TTL по auth_date
    auth_date = int(data.get("auth_date", "0"))
    if auth_date <= 0 or time.time() - auth_date > INITDATA_TTL_SEC:
        raise HTTPException(status_code=403, detail="initData expired")

    # user — JSON-строка
    user_json = data.get("user")
    if not user_json:
        raise HTTPException(status_code=400, detail="No user in initData")

    try:
        tg_user = json.loads(user_json)
    except Exception:
        raise HTTPException(status_code=400, detail="Corrupted user in initData")

    telegram_id = tg_user.get("id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Missing Telegram user id")

    # читаем/создаём в БД
    user = db.query(User).filter(User.id == telegram_id).first()
    if user:
        return user

    user = User(
        id=telegram_id,
        username=tg_user.get("username"),
        first_name=tg_user.get("first_name"),
        last_name=tg_user.get("last_name"),
        avatar_url=None,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
