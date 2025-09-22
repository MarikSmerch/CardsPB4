import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from sqlalchemy.orm import Session
from sqlalchemy import select

from bot.db import engine
from bot.db.models import CardType, Collection, CardTypeInCollection

# маппинг "корень имени файла → (имя, фамилия)"
FILE_TO_PERSON = {
    "alesya": ("Алеся", "Лопаткова"),
    "denis": ("Денис", "Кольцов"),
    "mark": ("Марк", "Соколов"),
    "katya": ("Екатерина", "Наймушина"),
    "dima": ("Дмитрий", "Матвеев"),
    "gosha": ("Георгий", "Максимов"),
    "ilya": ("Илья", "Полозков"),
    "lavr": ("Лаврентий", "Харитонов"),
    "lena": ("Елена", "Беляева"),
    "polina": ("Полина", "Шинкевич"),
    "sonya": ("Софья", "Комолова"),
    "alla": ("Алла", "Гончаренко"),
    "danya": ("Данил", "Бычков"),
    "fedorov": ("Денис", "Федоров"),
    "misha": ("Михаил", "Ламбрехт"),
    "pasha": ("Павел", "Шихирин"),
    "profkom": ("Профком", "ГУАП"),
    "rufina": ("Руфина", "Шарипова"),
    "tema": ("Артём", "Ледовских"),
    "timofey": ("Тимофей", "Кошев"),
    "vlad": ("Владислав", "Горбунов"),
}

PUBLIC_DIR = os.path.join(BASE_DIR, "frontend", "public", "cards")

def run():
    created, updated, skipped = 0, 0, 0

    with Session(engine) as db:
        collections = db.execute(select(Collection)).scalars().all()
        slug_to_col = {c.slug: c for c in collections}

        for col_slug, col in slug_to_col.items():
            col_dir = os.path.join(PUBLIC_DIR, col_slug)
            if not os.path.isdir(col_dir):
                print(f"[WARN] нет папки для коллекции {col_slug}")
                continue

            for fname in os.listdir(col_dir):
                if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                name = os.path.splitext(fname)[0].lower()
                core = name.replace("kartochka", "").strip(" _-")

                candidates = [core, name]

                if core.endswith(col_slug):
                    without = core[: -len(col_slug)].strip(" _-")
                    if without:
                        candidates.insert(0, without)

                person = None
                for key in candidates:
                    person = FILE_TO_PERSON.get(key)
                    if person:
                        break

                first, last = person
                ct = db.execute(
                    select(CardType).where(
                        (CardType.first_name == first) & (CardType.last_name == last)
                    )
                ).scalar_one_or_none()

                if not ct:
                    print(f"[WARN] нет CardType в БД: {first} {last}")
                    skipped += 1
                    continue

                path = f"/cards/{col_slug}/{fname}"
                link = db.execute(
                    select(CardTypeInCollection).where(
                        (CardTypeInCollection.card_type_id == ct.id) &
                        (CardTypeInCollection.collection_id == col.id)
                    )
                ).scalar_one_or_none()

                if not link:
                    db.add(CardTypeInCollection(
                        card_type_id=ct.id,
                        collection_id=col.id,
                        image_path=path
                    ))
                    created += 1
                else:
                    if link.image_path != path:
                        link.image_path = path
                        updated += 1

        db.commit()

    print(f"Memberships: created={created}, updated={updated}, skipped={skipped}")

if __name__ == "__main__":
    run()
