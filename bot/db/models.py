from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    vk_link = Column(String(255))
    avatar_url = Column(String(255))
    is_banned = Column(Boolean, default=False)
    ban_expiration = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)

    cards = relationship("Card", back_populates="user")


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    prize_id = Column(Integer, ForeignKey("prizes.id"))
    activated_by = Column(Integer, ForeignKey("users.id"))
    activated_at = Column(TIMESTAMP)
    is_activated = Column(Boolean, default=False)

    user = relationship("User", back_populates="cards")
    prize = relationship("Prize", back_populates="cards")


class Prize(Base):
    __tablename__ = "prizes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String)
    image_url = Column(String(255))

    cards = relationship("Card", back_populates="prize")
