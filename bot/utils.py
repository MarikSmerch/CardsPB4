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

# ---------------------- НОВОЕ: помощники ----------------------

def _compute_secret_key(token: str) -> bytes:
    """
    secret_key = HMAC_SHA256(bot_token, key="WebAppData")
    (Именно так требуется для Telegram Mini Apps)
    """
    return hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()


def _build_data_check_string(pairs: list[tuple[str, str]]) -> tuple[str, str]:
    """
    На вход — пары, полученные из СЫРОГО initData (query-string).
    Возвращает:
        data_check_string (str), received_hash (str)
    """
    received_hash = None
    kv_lines = []
    for k, v in pairs:
        if k == "hash":
            received_hash = v
        else:
            kv_lines.append(f"{k}={v}")

    if not received_hash:
        raise HTTPException(status_code=400, detail="Missing hash in initData")

    # Сортировка по ключу и склейка через '\n' — строго по спецификации
    kv_lines.sort(key=lambda s: s.split("=", 1)[0])
    return "\n".join(kv_lines), received_hash

# ---------------------- ОБНОВЛЕНО: основная функция ----------------------

def verify_telegram_init_data(init_data: str, db: Session) -> User:
    # 1) Разбираем СЫРОЙ initData в пары, не пере-сериализуя ничего
    try:
        pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid initData format")

    # Для дальнейшей работы удобно иметь dict (ключи уникальны в initData)
    data = dict(pairs)

    # 2) Строим data_check_string строго по правилам Mini Apps
    data_check_string, received_hash = _build_data_check_string(pairs)

    # 3) TTL по auth_date (из самого initData)
    try:
        auth_date = int(data.get("auth_date", "0"))
    except ValueError:
        raise HTTPException(status_code=403, detail="invalid auth_date")

    now_ts = int(time.time())
    if auth_date <= 0:
        raise HTTPException(status_code=403, detail="auth_date missing or invalid")

    delta = now_ts - auth_date
    if INITDATA_TTL_SEC > 0 and delta > INITDATA_TTL_SEC:
        raise HTTPException(
            status_code=403,
            detail=f"initData expired (delta={delta}s, ttl={INITDATA_TTL_SEC}s)"
        )

    # 4) Подпись: secret_key = HMAC_SHA256(bot_token, key="WebAppData")
    secret_key = _compute_secret_key(_bot_token())
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    # Сравнение в константном времени
    if not hmac.compare_digest(computed_hash, received_hash):
        # В 99% случаев это: неверный бот TOKEN / открыто не тем ботом / порча initData
        raise HTTPException(status_code=403, detail="Invalid Telegram signature (sig_mismatch)")

    # 5) Извлекаем user (это JSON-строка внутри initData), создаём/читаем из БД
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
