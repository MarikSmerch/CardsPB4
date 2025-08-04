import hmac
import hashlib
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from urllib.parse import parse_qsl
from bot.db import SessionLocal
from bot.db.models import User
from datetime import datetime

router = APIRouter()

BOT_TOKEN = os.getenv("TOKEN")


class InitDataPayload(BaseModel):
    initData: str


def parse_telegram_init_data(init_data_str: str):
    data = dict(parse_qsl(init_data_str, strict_parsing=True))
    hash_ = data.pop("hash", None)
    check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])

    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != hash_:
        raise ValueError("Invalid Telegram initData signature")

    return data


@router.post("/api/init")
def init(payload: InitDataPayload):
    try:
        data = parse_telegram_init_data(payload.initData)
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid initData")

    db = SessionLocal()
    telegram_id = int(data["user[id]"])
    username = data.get("user[username]")
    first_name = data.get("user[first_name]")

    user = db.query(User).filter_by(username=username).first()

    if not user:
        user = User(
            username=username,
            first_name=first_name,
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    db.close()

    return {
        "telegram_id": telegram_id,
        "username": username,
        "first_name": first_name
    }
