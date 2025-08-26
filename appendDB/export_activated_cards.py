# scripts/export_activated_cards.py
import os
import sys
import csv

# ── sys.path, чтобы импортировать bot.db.*
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from bot.db import SessionLocal
from bot.db.models import Card, CardType  # Card.is_activated, Card.code; CardType.first_name/last_name

DEFAULT_OUT = os.path.join(BASE_DIR, "data", "activated_cards.csv")

def export_activated_cards(output_path: str = DEFAULT_OUT) -> None:
    db = SessionLocal()
    try:
        q = (
            db.query(Card, CardType)
            .join(CardType, Card.card_type_id == CardType.id)
            .filter(Card.is_activated.is_(True))
            .order_by(CardType.last_name.asc(), CardType.first_name.asc(), Card.code.asc())
        )

        rows = [(ct.first_name or "", ct.last_name or "", card.code or "") for card, ct in q.all()]

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["first_name", "last_name", "code"])
            w.writerows(rows)

        print(f"OK: записано {len(rows)} строк в {output_path}")
    finally:
        db.close()

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    export_activated_cards(out)
