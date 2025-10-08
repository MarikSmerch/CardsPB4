from bot.db import SessionLocal
from bot.db.models import Card


def add_codes_from_file(filename):
    db = SessionLocal()
    added = 0
    skipped = 0

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            code = line.strip()
            if not code:
                continue

            exists = db.query(Card).filter_by(code=code).first()
            if exists:
                print(f"⏭ Пропущен (уже есть): {code}")
                skipped += 1
                continue

            new_card = Card(code=code)
            db.add(new_card)
            added += 1

    db.commit()
    db.close()

    print(f"✅ Добавлено: {added}, пропущено: {skipped}")


if __name__ == "__main__":
    add_codes_from_file("codes.txt")
