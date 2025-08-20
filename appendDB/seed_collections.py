import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from sqlalchemy.orm import Session
from sqlalchemy import select
from bot.db import engine
from bot.db.models import Collection

COLLECTIONS = [
    ("dizayn",  "Дизайнеры",                False),
    ("fiz",     "Физический носитель",      True),   # главная
    ("kopirayt","Копирайтеры",              False),
    ("kro",     "Креативно-ревизионный отдел", False),
    ("orgi",    "Организаторы",             False),
    ("osnova",  "Основа",                   False),
    ("preds",   "Председатель",             False),
    ("profkom", "Профком",                  False),
    ("spo",     "Социально-правовой отдел", False),
    ("sputnik", "Спутники",                 False),
]

def run():
    created, updated = 0, 0
    with Session(engine) as db:
        for slug, title, is_primary in COLLECTIONS:
            obj = db.execute(select(Collection).where(Collection.slug == slug)).scalar_one_or_none()
            if obj is None:
                db.add(Collection(slug=slug, title=title, is_primary=is_primary))
                created += 1
            else:
                obj.title = title
                obj.is_primary = is_primary
                updated += 1
        db.commit()
    print(f"Collections -> created: {created}, updated: {updated}")

if __name__ == "__main__":
    run()
