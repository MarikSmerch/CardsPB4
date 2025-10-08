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
from prizes_seed import seed_prizes  # <-- фикс импорта

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

# Маппинг кратких имён из файла → card_type_id
NAME_TO_CARDTYPE = {
    "Катя": 1, "Лавр": 2, "Лена": 3, "Марк": 4, "Миша": 5, "Паша": 6, "Полина": 7,
    "Профком": 8, "Руфина": 9, "Соня": 10, "Артем": 11, "Тим": 12, "Алеся": 13,
    "Алла": 14, "Влад": 15, "Гоша": 16, "Даня": 17, "Денис_К": 18, "Дима": 19,
    "Илья": 20, "Денис_Ф": 21,
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
    return pool

def main(path_to_txt, seed=42):
    rnd = random.Random(seed)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1) Справочник призов
        seed_prizes(db)

        # 2) Разбор входного файла
        rows = parse_txt(path_to_txt)
        if not rows:
            print("Файл пуст или ничего не распознано.")
            return

        # 3) by_person и выбор мансардного кода
        by_person = {}
        for r in rows:
            by_person.setdefault(r["name"], []).append(r["code"])

        mansarda_code = None
        if MANSARDA_PERSON in by_person and by_person[MANSARDA_PERSON]:
            mansarda_code = by_person[MANSARDA_PERSON][0]  # один код у Денис_К под мансарду
        else:
            print("ВНИМАНИЕ: нет строк для 'Денис_К' — мансарда никому не выдана.")

        # 4) Готовим общий список всех кодов (кроме мансарды), перемешиваем и мапим на пул призов
        prize_pool = build_prize_pool()
        # Общий список всех кодов:
        all_codes = []
        for nm, codes in by_person.items():
            for code in codes:
                if mansarda_code and code == mansarda_code:
                    continue
                all_codes.append((nm, code))
        rnd.shuffle(all_codes)  # <-- ключевой фикс: распределяем по всей совокупности, а не по первому человеку

        # Возьмём только столько кодов, сколько призов в пуле, и создадим карту code->prize_id
        rnd.shuffle(prize_pool)
        code_to_prize = {}
        for i in range(min(len(prize_pool), len(all_codes))):
            _, code = all_codes[i]
            code_to_prize[code] = prize_pool[i]

        # 5) Уже существующие коды
        existing = {c for (c,) in db.query(Card.code).all()}

        inserted = skipped = 0

        # 6) Создаём Card для каждого кода
        for nm, codes in by_person.items():
            card_type_id = NAME_TO_CARDTYPE.get(nm)
            if not card_type_id:
                print(f"[WARN] Неизвестное имя '{nm}' — нет маппинга на card_type_id. Пропускаю его коды.")
                continue

            for code in codes:
                if code in existing:
                    skipped += 1
                    continue

                if mansarda_code and code == mansarda_code:
                    prize_id = 6
                else:
                    prize_id = code_to_prize.get(code, DEFAULT_PRIZE)

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
        # Отладочная сводка
        used_non_default = len(code_to_prize)
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
