import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from bot.db import SessionLocal, engine
from bot.db.models import Card, CardType, Prize

CARDTYPE_ID_TO_ALIAS = {
    1: "Катя",         # Екатерина Наймушина
    2: "Лавр",         # Лаврентий Харитонов
    3: "Лена",         # Елена Беляева
    4: "Марк",         # Марк Соколов
    5: "Миша",         # Михаил Ламбрехт
    6: "Паша",         # Павел Шихирин
    7: "Полина",       # Полина Шинкевич
    8: "Профком",      # Профком ГУАП
    9: "Руфина",       # Руфина Шарипова
    10: "Соня",        # Софья Комолова
    11: "Артем",       # Артём Ледовских
    12: "Тим",         # Тимофей Кошев
    13: "Алеся",       # Алеся Лопаткова
    14: "Алла",        # Алла Гончаренко
    15: "Влад",        # Владислав Горбунов
    16: "Гоша",        # Георгий Максимов
    17: "Даня",        # Данил Бычков
    18: "Денис_К",     # Денис Кольцов
    19: "Дима",        # Дмитрий Матвеев
    20: "Илья",        # Илья Полозков
    21: "Денис_Ф",     # Денис Федоров
}

def alias_for(card_type: CardType) -> str:
    if card_type and card_type.id in CARDTYPE_ID_TO_ALIAS:
        return CARDTYPE_ID_TO_ALIAS[card_type.id]
    # Фолбэк: просто имя из БД, если встретится незамапленный тип
    if card_type:
        return card_type.first_name or f"cardtype_{card_type.id}"
    return "UNKNOWN"

def export_codes_with_prizes(output_path: str):
    db = SessionLocal()
    try:
        # Подтягиваем join-ом всё нужное, чтобы не было N+1
        q = (
            db.query(Card, CardType, Prize)
            .join(CardType, Card.card_type_id == CardType.id)
            .outerjoin(Prize, Card.prize_id == Prize.id)
            .order_by(CardType.id, Card.id)
        )

        rows = []
        for card, ct, prize in q.all():
            name = alias_for(ct)
            code = card.code
            prize_id = card.prize_id if card.prize_id is not None else 0
            rows.append((name, code, prize_id))

        # Сортируем стабильно по имени, затем по коду
        rows.sort(key=lambda t: (t[0], t[1]))

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for name, code, pid in rows:
                f.write(f"{name} -- {code} - {pid}\n")

        print(f"OK: записано {len(rows)} строк в {output_path}")
    finally:
        db.close()

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE_DIR, "data", "codes_with_names_and_prizes.txt")
    export_codes_with_prizes(out)
