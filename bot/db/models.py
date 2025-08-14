from sqlalchemy import Column,String, Boolean, ForeignKey, TIMESTAMP, func, BigInteger
from sqlalchemy import DateTime
from sqlalchemy.orm import relationship
from .base import Base

last_failed_at = Column(DateTime(timezone=True))
ban_until = Column(DateTime(timezone=True))
created_at = Column(DateTime(timezone=True), server_default=func.now())
ban_expiration = Column(DateTime(timezone=True))

# --- Типы/Коллекции ---


class CardType(Base):
    __tablename__ = "card_types"
    id = Column(BigInteger, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    cards = relationship("Card", back_populates="card_type")
    memberships = relationship("CardTypeInCollection", back_populates="card_type")


class Collection(Base):
    __tablename__ = "collections"
    id = Column(BigInteger, primary_key=True, index=True)
    slug = Column(String(100), unique=True, nullable=False)
    title = Column(String(150), nullable=False)
    is_primary = Column(Boolean, default=False)

    memberships = relationship("CardTypeInCollection", back_populates="collection")


class CardTypeInCollection(Base):
    __tablename__ = "cardtype_collections"
    card_type_id = Column(BigInteger, ForeignKey("card_types.id"), primary_key=True)
    collection_id = Column(BigInteger, ForeignKey("collections.id"), primary_key=True)
    image_path = Column(String(255), nullable=True)

    card_type = relationship("CardType", back_populates="memberships")
    collection = relationship("Collection", back_populates="memberships")


# --- Пользователь/Карты/Призы ---

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, index=True)  # Telegram user id
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    vk_link = Column(String(255))
    avatar_url = Column(String(255))

    is_banned = Column(Boolean, default=False)
    ban_expiration = Column(TIMESTAMP)

    failed_attempts = Column(BigInteger, default=0)
    last_failed_at = Column(TIMESTAMP)
    ban_until = Column(TIMESTAMP)

    created_at = Column(TIMESTAMP, server_default=func.now())
    cards = relationship("Card", back_populates="user")


class Card(Base):
    __tablename__ = "cards"
    id = Column(BigInteger, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)

    card_type_id = Column(BigInteger, ForeignKey("card_types.id"), nullable=False)
    prize_id = Column(BigInteger, ForeignKey("prizes.id"))
    activated_by = Column(BigInteger, ForeignKey("users.id"))
    activated_at = Column(TIMESTAMP)
    is_activated = Column(Boolean, default=False)

    user = relationship("User", back_populates="cards")
    prize = relationship("Prize", back_populates="cards")
    card_type = relationship("CardType", back_populates="cards")


class Prize(Base):
    __tablename__ = "prizes"
    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String)
    cards = relationship("Card", back_populates="prize")
