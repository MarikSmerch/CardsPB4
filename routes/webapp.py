from fastapi import APIRouter, Request, HTTPException
from bot.db import SessionLocal
from bot.db_requests import get_or_create_user_by_telegram_init_data

router = APIRouter()


@router.post("/init")
async def init(request: Request):
    data = await request.json()
    init_data = data.get("initData")

    if not init_data:
        raise HTTPException(status_code=400, detail="Missing initData")

    db = SessionLocal()
    user = get_or_create_user_by_telegram_init_data(db, init_data)
    db.close()

    return {
        "username": user.username,
        "telegram_id": user.id,
        "avatar_url": user.avatar_url,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


@router.post("/activate")
async def activate_card(request: Request):
    data = await request.json()
    code = data.get("code")
    telegram_id = data.get("telegram_id")

    if not code or not telegram_id:
        raise HTTPException(status_code=400, detail="Missing code or telegram_id")

    db = SessionLocal()

    from bot.db.models import Card

    card = db.query(Card).filter_by(code=code).first()

    if not card:
        db.close()
        return {"message": "Код не найден."}

    if card.is_activated:
        db.close()
        return {"message": "Код уже активирован."}

    card.activated_by = telegram_id
    card.is_activated = True
    from datetime import datetime
    card.activated_at = datetime.utcnow()
    db.commit()
    db.close()

    return {"message": "Код успешно активирован! Поздравляем 🎉"}