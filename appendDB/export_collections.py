# export_collections.py
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
from bot.db.models import User, Card, CardType
from bot.db import engine

import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Настройте URL вашей БД

Session = sessionmaker(bind=engine)


# --- НАЗНАЧЕНИЕ НИКОВ/КРАТКИХ ИМЕН на реальные имена из таблицы card_types ---
# Эти строки соответствуют списку card_types, который вы прислали.
# Если в вашей БД имена отличаются — поправьте словарь.
COLLECTIONS_IDS = {
    "физические": list(range(1, 22)),  # все 21 карточка: 1..21

    "основа": [13, 14, 15, 16, 18, 19, 6],   # алеся, алла, владислав, гоша, денис кольцов, дима, паша

    "дизайнеры": [13, 16, 19, 3, 20, 2, 7, 10],  # алеся, гоша, дима, елена, илья, лаврентий, полина, софья(соня)

    "копирайтеры": [13, 11, 19, 1, 9],  # алеся, тема(=артём=11), дима, катя, руфина

    "орги": [13, 14, 11, 16, 17, 18, 19, 3, 20, 2, 4, 6, 9, 10, 12],
    # алеся, алла, тема(артём), гоша, даня, денис кольцов, дима, лена, илья, лаврентий, марк, паша, руфина, софья, тимофей

    "профком": [14, 18, 21, 6, 8],  # алла, денис кольцов, денис федоров(21), паша, профком гуап(8)

    "социально правовой отдел": [11, 16, 18, 20, 5, 6],  # тема(11), гоша, денис кольцов, илья, миша, паша

    "спутники": [13, 14, 11, 16, 17, 19, 20, 2, 4, 5, 6, 7, 9]
    # алеся, алла, тема, гоша, данил, дима, илья, лаврентий, марк, миша, паша, полина, руфина
}

def export_to_markdown(output_path="collections_export.md"):
    session = Session()
    try:
        # Получим общее число card_types (на случай логики "все карточки")
        total_cardtypes_count = session.query(CardType).count()

        # Получим всех пользователей (или можно только тех, у кого есть карты)
        users = session.query(User).all()

        # Для каждой коллекции — список (user, last_date)
        collection_users = {col: [] for col in COLLECTIONS_IDS.keys()}

        for user in users:
            # получаем активированные карточки пользователя
            activated_cards = session.query(Card).filter(
                Card.activated_by == user.id,
                Card.is_activated == True
            ).all()

            if not activated_cards:
                continue

            activated_ct_ids = {c.card_type_id for c in activated_cards}
            last_activation_overall = max((c.activated_at for c in activated_cards if c.activated_at), default=None)

            user_has_all = len(activated_ct_ids) >= total_cardtypes_count

            for col_name, ct_ids in COLLECTIONS_IDS.items():
                if user_has_all:
                    if last_activation_overall:
                        collection_users[col_name].append((user, last_activation_overall))
                else:
                    inter = activated_ct_ids.intersection(set(ct_ids))
                    if inter:
                        # найдем последнюю activation дату только среди карточек этой коллекции
                        last_date = None
                        for c in activated_cards:
                            if c.card_type_id in inter and c.activated_at:
                                if last_date is None or c.activated_at > last_date:
                                    last_date = c.activated_at
                        if last_date:
                            collection_users[col_name].append((user, last_date))

        # Сортируем по дате (от дальней к ближайшей => desc)
        for col in collection_users:
            collection_users[col].sort(key=lambda p: p[1], reverse=True)


        # Запись в markdown
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# Экспорт коллекций — {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
            for col_name, entries in collection_users.items():
                f.write(f"## {col_name}\n\n")
                if not entries:
                    f.write("_Никто ещё не активировал карточки этой коллекции._\n\n")
                    continue
                for user, last_dt in entries:
                    dt_str = last_dt.strftime("%d.%m.%Y") if last_dt else "—"
                    username = f"@{user.username}" if user.username else f"{user.first_name or ''} {user.last_name or ''}".strip()
                    f.write(f"*{user.id}* {username} - {dt_str}\n")
                f.write("\n")
        print("Экспорт завершён:", output_path)
    finally:
        session.close()

if __name__ == "__main__":
    export_to_markdown()
