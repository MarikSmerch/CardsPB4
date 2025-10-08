import os, sys, re, random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from bot.db import SessionLocal, engine
from bot.db.models import Base, Card
from prizes_seed import seed_prizes

QUOTAS = {1:25, 2:10, 4:5, 3:5, 5:5, 6:1}
DEFAULT_PRIZE = 0
MANSARDA_PERSON = "Денис_К"

LINE_RE = re.compile(r"^\s*(?P<name>[^-]+?)\s*--\s*(?P<code>[A-Z0-9-]{5,})\s*$")

def parse_txt(path):
    rows=[]
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f,1):
            line=line.strip()
            if not line: continue
            m=LINE_RE.match(line)
            if not m:
                print(f"[WARN] строка {i} пропущена: {line}")
                continue
            rows.append({"name":m.group("name"),"code":m.group("code")})
    return rows

def build_pool(rnd):
    pool=[]
    for pid, qty in QUOTAS.items():
        if pid==6: continue
        pool.extend([pid]*qty)
    rnd.shuffle(pool)
    return pool

def main(path_to_txt, seed=42):
    rnd = random.Random(seed)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_prizes(db)  # гарантируем призы id 0..6

        rows = parse_txt(path_to_txt)
        if not rows:
            print("Файл пуст или не распознан."); return

        # код под мансарду
        mansarda_code = next((r["code"] for r in rows if r["name"]==MANSARDA_PERSON), None)

        # карты, которые реально есть в БД
        codes = [r["code"] for r in rows]
        db_cards = db.query(Card).filter(Card.code.in_(codes)).all()
        code_to_card = {c.code: c for c in db_cards}

        # список для распределения (кроме мансарды)
        distrib = [c for c in code_to_card.keys() if not (mansarda_code and c==mansarda_code)]
        rnd.shuffle(distrib)

        prize_pool = build_pool(rnd)
        # сопоставление код->приз из пула; лишние коды получат 0
        code_to_prize = {distrib[i]: prize_pool[i] for i in range(min(len(prize_pool), len(distrib)))}

        # проставляем
        updated=0
        for code, card in code_to_card.items():
            if mansarda_code and code==mansarda_code:
                card.prize_id = 6
            else:
                card.prize_id = code_to_prize.get(code, DEFAULT_PRIZE)
            updated += 1

        db.commit()
        print(f"OK. Обновлено карт: {updated}. Мансарда: {mansarda_code or 'не выдана'}")
        print(f"Ненулевых по квотам выдано: {len(code_to_prize)}; остальным присвоено {DEFAULT_PRIZE}.")
    finally:
        db.close()

if __name__=="__main__":
    if len(sys.argv)<2:
        print("Использование: python scripts/reassign_prizes.py data/codes_with_names.txt [seed]")
        sys.exit(1)
    path=sys.argv[1]
    seed=int(sys.argv[2]) if len(sys.argv)>2 else 42
    main(path, seed)