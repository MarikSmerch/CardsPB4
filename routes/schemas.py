from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List


# --- Входы ---

class InitIn(BaseModel):
    initData: str


class ActivateIn(BaseModel):
    initData: str
    code: str = Field(min_length=3, max_length=64)


class ProfileUpdateIn(BaseModel):
    initData: str
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    vk_link: Optional[str] = Field(default=None, max_length=255)


# --- Выходы ---

class ProfileOut(BaseModel):
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    vk_link: Optional[str]
    avatar_url: Optional[HttpUrl]
    is_banned: bool
    ban_until: Optional[str]


class ActivateOut(BaseModel):
    ok: bool
    message: str
    activated_at: Optional[str] = None
    already_owned: Optional[bool] = None
    prize: Optional[dict] = None
    card_type: Optional[dict] = None


class CollectionBriefOut(BaseModel):
    id: int
    slug: str
    title: str
    is_primary: bool


class CardTypeInCollectionOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    image_path: Optional[str]
    collected: bool


class CollectionWithCardsOut(BaseModel):
    id: int
    slug: str
    title: str
    is_primary: bool
    items: List[CardTypeInCollectionOut]


class PrizeCountOut(BaseModel):
    id: int
    title: str
    count: int


class CardTypeOut(BaseModel):
    id: int
    first_name: str
    last_name: str


class CardBriefOut(BaseModel):
    code: str
    activated_at: str
    card_type: CardTypeOut
    prize: Optional[dict] = None
