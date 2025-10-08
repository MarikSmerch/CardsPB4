from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, exists, func, literal_column
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from bot.db import get_db
from bot.utils import verify_telegram_init_data
from bot.db.models import User, Card, Prize, Collection, CardType, CardTypeInCollection
from .schemas import (
    InitIn, ActivateIn, ActivateOut,
    ProfileOut, ProfileUpdateIn,
    CollectionWithCardsOut, CollectionBriefOut, CardTypeInCollectionOut,
    CardBriefOut, CardTypeOut, PrizeCountOut, PrizeOut
)

import os
import requests
from pathlib import Path
from time import time
from typing import Optional


router = APIRouter()

# Параметры банов
FAIL_WINDOW_SEC = int(3600)
MAX_FAILS = int(5)
BAN_SEC = int(3600)


# Настройки для аватарок
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_DIR = Path(__file__).resolve().parent.parent
AVATAR_DIR = BASE_DIR / "static" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
AVATAR_TTL = 24*3600


def now_utc():
    return datetime.now(timezone.utc)


def _normalize_vk_link(vk: str | None) -> str | None:
    if not vk:
        return None
    vk = vk.strip()
    if not vk:
        return None
    # Приводим к виду https://vk.com/<id|username>
    if vk.startswith("http://"):
        vk = "https://" + vk[len("http://"):]
    if vk.startswith("vk.com/"):
        vk = "https://" + vk
    return vk


def _register_fail(user: User, now: datetime):
    if user.last_failed_at and (now - user.last_failed_at).total_seconds() <= FAIL_WINDOW_SEC:
        user.failed_attempts = (user.failed_attempts or 0) + 1
    else:
        user.failed_attempts = 1
    user.last_failed_at = now
    if user.failed_attempts >= MAX_FAILS:
        user.ban_until = now + timedelta(seconds=BAN_SEC)
        user.failed_attempts = 0
        user.last_failed_at = None


def _clear_fail(user: User):
    user.failed_attempts = 0
    user.last_failed_at = None
    user.ban_until = None
    # старые флаги на всякий случай
    user.is_banned = False
    user.ban_expiration = None


def _local_avatar_path(tg_id: int) -> Path:
    return AVATAR_DIR / f"{tg_id}.jpg"


def _is_local_avatar_fresh(path: Path) -> bool:
    return path.exists() and (time() - path.stat().st_mtime) < AVATAR_TTL


def _download_telegram_avatar(tg_id: int) -> Optional[str]:
    if not BOT_TOKEN:
        return None
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUserProfilePhotos",
            params={"user_id": tg_id, "limit": 1},
            timeout=10
        )
        r.raise_for_status()
        photos = r.json().get("result", {}).get("photos", [])
        if not photos:
            return None
        file_id = photos[0][-1]["file_id"]

        r = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
            params={"file_id": file_id},
            timeout=10
        )
        r.raise_for_status()
        file_path = r.json().get("result", {}).get("file_path")
        if not file_path:
            return None

        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        rr = requests.get(file_url, stream=True, timeout=20)
        rr.raise_for_status()
        local = _local_avatar_path(tg_id)
        with open(local, "wb") as f:
            for chunk in rr.iter_content(1024):
                if chunk:
                    f.write(chunk)
        return f"/static/avatars/{local.name}"

    except Exception as e:
        print("Ошибка при скачивании аватара:", e)
        return None


@router.post("/init", response_model=ProfileOut)
def init(payload: InitIn, db: Session = Depends(get_db)):
    user = verify_telegram_init_data(payload.initData, db)

    avatar_url: Optional[str] = None
    tg_id = getattr(user, "id") or getattr(user, "telegram_id", None)
    if tg_id:
        local_p = _local_avatar_path(tg_id)
        if _is_local_avatar_fresh(local_p):
            avatar_url = f"/static/avatars/{local_p.name}"
        else:
            downloaded = _download_telegram_avatar(tg_id)
            if downloaded:
                avatar_url = downloaded

    return ProfileOut(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        vk_link=getattr(user, "vk_link", None),
        avatar_url=avatar_url,
        is_banned=False,
        ban_until=None
    )


@router.post("/activate", response_model=ActivateOut, response_model_exclude_none=False)
def activate(payload: ActivateIn, db: Session = Depends(get_db)):
    user = verify_telegram_init_data(payload.initData, db)
    now = now_utc()
    

    if user.ban_until and now < user.ban_until:
        remain = int((user.ban_until - now).total_seconds())
        raise HTTPException(status_code=429, detail=f"Слишком много попыток. Подождите {remain} сек.")

    card = db.execute(
        select(Card).where(Card.code == payload.code).with_for_update()
    ).scalar_one_or_none()

    if card is None:
        _register_fail(user, now)
        db.add(user)
        db.commit()
        raise HTTPException(status_code=400, detail="Неверный код")

    prize = PrizeOut(
        id=card.prize.id,
        title=card.prize.title,
        description=card.prize.description
    ) if card.prize else None

    if card.is_activated:
        if card.activated_by == user.id:
            _clear_fail(user)
            db.add(user)
            db.commit()
            return ActivateOut(
                ok=True, message="Код уже активирован",
                activated_at=card.activated_at.isoformat() if card.activated_at else None,
                already_owned=True,
                prize=prize,
                card_type={
                    "id": card.card_type.id,
                    "first_name": card.card_type.first_name,
                    "last_name": card.card_type.last_name
                }
            )
        _register_fail(user, now)
        db.add(user)
        db.commit()
        raise HTTPException(status_code=409, detail="Код уже активирован")

    card.is_activated = True
    card.activated_by = user.id
    card.activated_at = now
    _clear_fail(user)
    db.add_all([card, user])
    db.commit()

    return ActivateOut(
        ok=True,
        message="Код активирован",
        activated_at=card.activated_at.isoformat(),
        prize=prize,
        card_type={
            "id": card.card_type.id,
            "first_name": card.card_type.first_name,
            "last_name": card.card_type.last_name
        }
    )


@router.post("/collections", response_model=list[CollectionWithCardsOut], response_model_exclude_none=False)
def collections(payload: InitIn, db: Session = Depends(get_db)):
    user = verify_telegram_init_data(payload.initData, db)

    order = ["fiz", "osnova", "dizayn", "kopirayt", "kro", "orgi", "preds", "profkom", "spo", "sputnik"]
    cols = db.execute(select(Collection)).scalars().all()
    cols.sort(key=lambda c: (order.index(c.slug) if c.slug in order else 999, c.id))

    result: list[CollectionWithCardsOut] = []

    for col in cols:
        rows = db.execute(
            select(
                CardType.id.label("ct_id"),
                CardType.first_name.label("fn"),
                CardType.last_name.label("ln"),
                CardType.description.label("ct_desc"),
                CardTypeInCollection.image_path.label("img"),
            )
            .join(CardType, CardType.id == CardTypeInCollection.card_type_id)
            .where(CardTypeInCollection.collection_id == col.id)
        ).all()

        items: list[CardTypeInCollectionOut] = []
        for r in rows:
            collected = db.execute(
                select(exists().where(
                    Card.card_type_id == r.ct_id,
                    Card.is_activated == True,
                    Card.activated_by == user.id
                ))
            ).scalar()
            print("ct_id=", r.ct_id, "desc_len=", 0 if r.ct_desc is None else len(r.ct_desc or ""))
            items.append(CardTypeInCollectionOut(
                id=r.ct_id,
                first_name=r.fn,
                last_name=r.ln,
                description=(r.ct_desc if r.ct_desc is not None else ""),
                image_path=r.img,
                collected=bool(collected),
            ))

        items.sort(key=lambda x: (x.first_name.lower(), x.last_name.lower()))
        result.append(CollectionWithCardsOut(
            id=col.id, slug=col.slug, title=col.title, is_primary=col.is_primary, items=items
        ))

    return result


@router.post("/me/cards", response_model=list[CardBriefOut])
def my_cards(payload: InitIn, db: Session = Depends(get_db)):
    user = verify_telegram_init_data(payload.initData, db)
    rows = db.execute(
        select(Card).where(Card.activated_by == user.id, Card.is_activated == True)  # noqa: E712
    ).scalars().all()

    out: list[CardBriefOut] = []
    for c in rows:
        out.append(CardBriefOut(
            code=c.code,
            activated_at=c.activated_at.isoformat() if c.activated_at else "",
            card_type=CardTypeOut(
                id=c.card_type.id, first_name=c.card_type.first_name, last_name=c.card_type.last_name
            ),
            prize=PrizeOut(id=c.prize.id, title=c.prize.title, description=c.prize.description) if c.prize else None
        ))
    return out


@router.post("/me/prizes", response_model=list[PrizeCountOut])
def my_prizes(payload: InitIn, db: Session = Depends(get_db)):
    user = verify_telegram_init_data(payload.initData, db)
    rows = db.execute(
        select(Prize.id, Prize.title, func.count(Card.id))
        .join(Card, Card.prize_id == Prize.id)
        .where(Card.activated_by == user.id, Card.is_activated == True)  # noqa: E712
        .group_by(Prize.id, Prize.title)
    ).all()
    return [PrizeCountOut(id=r[0], title=r[1], count=r[2]) for r in rows]


@router.get("/me", response_model=ProfileOut)
def get_profile(initData: str, db: Session = Depends(get_db)):
    user = verify_telegram_init_data(initData, db)
    is_banned = bool(user.ban_until and now_utc() < user.ban_until)
    return ProfileOut(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        vk_link=user.vk_link,
        avatar_url=user.avatar_url,
        is_banned=is_banned,
        ban_until=user.ban_until.isoformat() if user.ban_until else None
    )


@router.post("/me", response_model=ProfileOut)
def update_profile(payload: ProfileUpdateIn, db: Session = Depends(get_db)):
    # verify_telegram_init_data возвращает User из БД
    user = verify_telegram_init_data(payload.initData, db)

    # 1) Имя/фамилия: чистим пробелы; пустые строки -> NULL
    if payload.first_name is not None:
        fn = (payload.first_name or "").strip()[:100]
        user.first_name = fn or None

    if payload.last_name is not None:
        ln = (payload.last_name or "").strip()[:100]
        user.last_name = ln or None

    # 2) VK: нормализуем к https://vk.com/...; пустое -> NULL
    if payload.vk_link is not None:
        user.vk_link = _normalize_vk_link(payload.vk_link)

    db.add(user)
    db.commit()
    db.refresh(user)

    return ProfileOut(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        vk_link=user.vk_link,
        avatar_url=user.avatar_url,
        is_banned=bool(getattr(user, "ban_until", None) and now_utc() < user.ban_until),
        ban_until=user.ban_until.isoformat() if getattr(user, "ban_until", None) else None,
    )


@router.post("/_echo_init")
def echo_init(payload: dict):
    # просто лог/эхо на время отладки
    init_data = payload.get("initData", "")
    print("[_echo_init] initData head:", init_data[:160])
    return {"len": len(init_data)}
