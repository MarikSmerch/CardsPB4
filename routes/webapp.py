from fastapi import APIRouter, Request, HTTPException
from bot.db import SessionLocal
from bot.db_requests import get_or_create_user_by_telegram_init_data

router = APIRouter(prefix="/api")


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
