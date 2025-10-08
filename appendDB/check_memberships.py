# -*- coding: utf-8 -*-
import os, sys, csv
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from sqlalchemy.orm import Session
from sqlalchemy import select
from bot.db import engine
from bot.db.models import CardType, Collection, CardTypeInCollection

REPORT_PATH = os.path.join(BASE_DIR, "appendDB", "membership_report.csv")

def run():
    with Session(engine) as db:
        cols = db.execute(select(Collection)).scalars().all()
        id2col = {c.id: c for c in cols}
        slug2col = {c.slug: c for c in cols}
        fiz_id = slug2col["fiz"].id if "fiz" in slug2col else None

        cts = db.execute(select(CardType)).scalars().all()

        rows = []
        missing_fiz = []
        total_links = 0

        for ct in cts:
            links = db.execute(
                select(CardTypeInCollection).where(CardTypeInCollection.card_type_id == ct.id)
            ).scalars().all()

            total_links += len(links)
            slugs = [id2col[l.collection_id].slug for l in links]
            titles = [id2col[l.collection_id].title for l in links]
            images = [l.image_path or "" for l in links]

            if fiz_id and all(l.collection_id != fiz_id for l in links):
                missing_fiz.append(f"{ct.last_name} {ct.first_name}")

            rows.append({
                "last_name": ct.last_name,
                "first_name": ct.first_name,
                "collections_slugs": "|".join(slugs),
                "collections_titles": "|".join(titles),
                "images": "|".join(images),
                "count": len(links),
            })

    # write CSV
    with open(REPORT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["last_name","first_name","count","collections_slugs","collections_titles","images"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"✅ Report saved: {REPORT_PATH}")
    print(f"Всего карточек: {len(rows)}; всего связей: {total_links}")
    if missing_fiz:
        print("\n⚠️ Нет картинки в главной коллекции (fiz) для:")
        for name in missing_fiz:
            print("  -", name)
    else:
        print("🎉 У всех карточек есть запись в fiz")

if __name__ == "__main__":
    run()
