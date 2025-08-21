import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from sqlalchemy import select
from bot.db.models import Prize

PRIZES = [
    (0, "ничего", "К сожалению, ничего"),
    (1, "брелок", "Брелок ПБ4"),
    (2, "брелок-касатка", "Брелок-касатка"),
    (3, "шоппер", "Шоппер с касаткой"),
    (4, "пельмени", "Вкусные пельмени"),
    (5, "пенал", "Пенал-касатка"),
    (6, "мансарда", "Проходка на мансарду"),
]

def seed_prizes(db):
    """Идемпотентная заливка призов с фикс. ID 0..6."""
    existing = {pid for (pid,) in db.execute(select(Prize.id)).all()}
    for pid, title, descr in PRIZES:
        if pid not in existing:
            db.add(Prize(id=pid, title=title, description=descr))
    db.commit()
