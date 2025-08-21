# scripts/import_codes_from_txt.py
import os
import re
import sys
import random

# ── sys.path, чтобы импортировать bot.db.*
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from bot.db import SessionLocal, engine
from bot.db.models import Base, Card
from prizes_seed import seed_prizes

# ====== НАСТРОЙКИ ======
# Квоты:
QUOTAS = {
    1: 25,  # брелок
    2: 10,  # брелок-касатка
    4:  5,  # пельмени
    3:  5,  # шоппер
    5:  5,  # пенал
    6:  1,  # мансарда — строго у Денис_К
}
DEFAULT_PRIZE = 0

# Имя для мансарды:
MANSARDA_PERSON = "Денис_К"

# Маппинг кратких имён из файла → card_type_id (из твоей БД)
NAME_TO_CARDTYPE = {
    "Катя": 1,       # Екатерина Наймушина
    "Лавр": 2,       # Лаврентий Харитонов
    "Лена": 3,       # Елена Беляева
    "Марк": 4,       # Марк Соколов
    "Миша": 5,       # Михаил Ламбрехт
    "Паша": 6,       # Павел Шихирин
    "Полина": 7,     # Полина Шинкевич
    "Профком": 8,    # Профком ГУАП
    "Руфина": 9,     # Руфина Шарипова
    "Соня": 10,      # Софья Комолова
    "Артем": 11,     # Артём Ледовских
    "Тим": 12,       # Тимофей Кошев
    "Алеся": 13,     # Алеся Лопаткова
    "Алла": 14,      # Алла Гончаренко
    "Влад": 15,      # Владислав Горбунов
    "Гоша": 16,      # Георгий Максимов
    "Даня": 17,      # Данил Бычков
    "Денис_К": 18,   # Денис Кольцов
    "Дима": 19,      # Дмитрий Матвеев
    "Илья": 20,      # Илья Полозков
    "Денис_Ф": 21,   # Денис Федоров
}

LINE_RE = re.compile(r"^\s*(?P<name>[^-]+?)\s*--\s*(?P<code>[A-Z0-9-]{5,})\s*$")

def parse_txt(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            m = LINE_RE.match(line)
            if not m:
                print(f"[WARN] Строка {i} пропущена (не распознана): {line}")
                continue
            rows.append({"name": m.group("name"), "code": m.group("code")})
    return rows

def build_prize_pool():
    pool = []
    for pid, qty in QUOTAS.items():
        if pid == 6:
            continue  # мансарду не кладём в пул — именная
        pool.extend([pid] * qty)
    random.shuffle(pool)
    return pool

def main(path_to_txt, seed=42):
    random.seed(seed)
    # На случай чистой БД
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1) Зальём справочник призов
        seed_prizes(db)

        # 2) Разберём входной файл
        rows = parse_txt(path_to_txt)
        if not rows:
            print("Файл пуст или ничего не распознано.")
            return

        # 3) Сгруппируем коды по человекy и найдём цель для мансарды
        by_person = {}
        for r in rows:
            nm = r["name"]
            by_person.setdefault(nm, []).append(r["code"])

        mansarda_code = None
        if MANSARDA_PERSON in by_person and by_person[MANSARDA_PERSON]:
            mansarda_code = by_person[MANSARDA_PERSON][0]  # первый код Дениса_К
        else:
            print("ВНИМАНИЕ: в файле нет строк для 'Денис_К' — мансарда никому не выдана.")

        # 4) Подготовим пул призов
        prize_pool = build_prize_pool()
        pool_idx = 0

        # 5) Уже существующие коды в БД
        existing = {c for (c,) in db.query(Card.code).all()}

        inserted = skipped = 0

        # 6) Идём по всем строкам и создаём Card
        for nm, codes in by_person.items():
            card_type_id = NAME_TO_CARDTYPE.get(nm)
            if not card_type_id:
                print(f"[WARN] Неизвестное имя '{nm}' — нет маппинга на card_type_id. Пропускаю его коды.")
                continue

            for code in codes:
                if code in existing:
                    skipped += 1
                    continue

                # Выбор приза
                if mansarda_code and code == mansarda_code:
                    prize_id = 6
                elif pool_idx < len(prize_pool):
                    prize_id = prize_pool[pool_idx]
                    pool_idx += 1
                else:
                    prize_id = DEFAULT_PRIZE

                db.add(Card(
                    code=code,
                    card_type_id=card_type_id,
                    prize_id=prize_id,
                    is_activated=False,
                ))
                inserted += 1

        db.commit()
        print(f"Готово. Добавлено: {inserted}, пропущено (дубликаты): {skipped}.")
        if mansarda_code:
            print(f"«Мансарда» выдана коду: {mansarda_code} ({MANSARDA_PERSON})")
        # Сводка по фактической раздаче (по желанию можно расширить)
        used_non_default = min(pool_idx, len(prize_pool))
        print(f"Выдано призов по квотам (без 'ничего'): {used_non_default}; остальным — 0 (ничего).")

    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python scripts/import_codes_from_txt.py data/codes_with_names.txt [random_seed]")
        sys.exit(1)
    path = sys.argv[1]
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    main(path, s)
