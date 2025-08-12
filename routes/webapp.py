from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, exists, func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from bot.db import get_db
from bot.utils import verify_telegram_init_data
from bot.db.models import User, Card, Prize, Collection, CardType, CardTypeInCollection
from .schemas import (
    InitIn, ActivateIn, ActivateOut,
    ProfileOut, ProfileUpdateIn,
    CollectionWithCardsOut, CollectionBriefOut, CardTypeInCollectionOut,
    CardBriefOut, CardTypeOut, PrizeCountOut
)

router = APIRouter()

# Параметры банов
FAIL_WINDOW_SEC = int(3600)
MAX_FAILS = int(5)
BAN_SEC = int(3600)


def now_utc():
    return datetime.now(timezone.utc)


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


@router.post("/init", response_model=ProfileOut)
def init(payload: InitIn, db: Session = Depends(get_db)):
    user = verify_telegram_init_data(payload.initData, db)
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


@router.post("/activate", response_model=ActivateOut)
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

    if card.is_activated:
        if card.activated_by == user.id:
            _clear_fail(user)
            db.add(user)
            db.commit()
            return ActivateOut(
                ok=True, message="Код уже активирован вами",
                activated_at=card.activated_at.isoformat() if card.activated_at else None,
                already_owned=True,
                prize={"id": card.prize.id, "title": card.prize.title} if card.prize else None,
                card_type={"id": card.card_type.id, "first_name": card.card_type.first_name, "last_name": card.card_type.last_name}
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
        ok=True, message="Код активирован",
        activated_at=card.activated_at.isoformat(),
        prize={"id": card.prize.id, "title": card.prize.title} if card.prize else None,
        card_type={"id": card.card_type.id, "first_name": card.card_type.first_name, "last_name": card.card_type.last_name}
    )


@router.post("/collections", response_model=list[CollectionWithCardsOut])
def collections(payload: InitIn, db: Session = Depends(get_db)):
    user = verify_telegram_init_data(payload.initData, db)
    cols = db.execute(select(Collection)).scalars().all()

    result: list[CollectionWithCardsOut] = []
    for col in cols:
        memberships = db.execute(
            select(CardTypeInCollection, CardType)
            .join(CardType, CardType.id == CardTypeInCollection.card_type_id)
            .where(CardTypeInCollection.collection_id == col.id)
        ).all()

        items: list[CardTypeInCollectionOut] = []
        for m, ct in memberships:
            collected = db.execute(
                select(exists().where(
                    Card.card_type_id == ct.id,
                    Card.is_activated == True,          # noqa: E712
                    Card.activated_by == user.id
                ))
            ).scalar()
            items.append(CardTypeInCollectionOut(
                id=ct.id, first_name=ct.first_name, last_name=ct.last_name,
                image_path=m.image_path, collected=bool(collected)
            ))

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
            prize={"id": c.prize.id, "title": c.prize.title} if c.prize else None
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
    user = verify_telegram_init_data(payload.initData, db)
    if payload.first_name is not None:
        user.first_name = payload.first_name.strip() or None
    if payload.last_name is not None:
        user.last_name = payload.last_name.strip() or None
    if payload.vk_link is not None:
        vk = payload.vk_link.strip()
        user.vk_link = vk or None
    db.add(user)
    db.commit()
    return ProfileOut(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        vk_link=user.vk_link,
        avatar_url=user.avatar_url,
        is_banned=bool(user.ban_until and now_utc() < user.ban_until),
        ban_until=user.ban_until.isoformat() if user.ban_until else None
    )
