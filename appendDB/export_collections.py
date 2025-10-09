# export_collections_debug.py
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from bot.db.models import User, Card, CardType
from bot.db import engine

Session = sessionmaker(bind=engine)

# --- Коллекции как списки ID (взято из твоей таблицы 1..21) ---
COLLECTIONS_IDS = {
    "физические": list(range(1, 22)),  # все 21 карточка: 1..21
    "основа": [13, 14, 15, 16, 18, 19, 6],
    "дизайнеры": [13, 16, 19, 3, 20, 2, 7, 10],
    "копирайтеры": [13, 11, 19, 1, 9],
    "орги": [13, 14, 11, 16, 17, 18, 19, 3, 20, 2, 4, 6, 9, 10, 12],
    "профком": [14, 18, 21, 6, 8],
    "социально правовой отдел": [11, 16, 18, 20, 5, 6],
    "спутники": [13, 14, 11, 16, 17, 19, 20, 2, 4, 5, 6, 7, 9]
}

# Минимальное количество совпадающих карточек, чтобы считать коллекцию "активированной"
# По умолчанию 1 (как у тебя было). Поставь >1, если хочешь быть строже.
MIN_MATCH_COUNT = 1

def build_user_cards(session):
    """
    Возвращает:
      user_map: { user_id: User_obj }
      user_cards: { user_id: { card_type_id: activated_at (datetime) } }
    """
    # Берём все активированные карточки
    cards = session.query(Card).filter(Card.is_activated == True).all()

    user_map = {}
    user_cards = {}
    for c in cards:
        uid = c.activated_by
        if uid is None:
            continue
        user = session.query(User).get(uid)
        if user is None:
            # странный случай — карта привязана к несуществующему пользователю
            continue
        user_map[uid] = user
        user_cards.setdefault(uid, {})
        # если одна и та же карточка активировалась несколько раз, возьмём max дату
        prev = user_cards[uid].get(c.card_type_id)
        if prev is None or (c.activated_at and c.activated_at > prev):
            user_cards[uid][c.card_type_id] = c.activated_at
    return user_map, user_cards

def validate_collections(session):
    """Проверка, что в COLLECTIONS_IDS используются реальные card_type id"""
    ct_ids_in_db = {ct.id for ct in session.query(CardType.id).all()}
    bad = {}
    for col, ids in COLLECTIONS_IDS.items():
        unknown = [i for i in ids if i not in ct_ids_in_db]
        if unknown:
            bad[col] = unknown
    return bad

def export(output_md="collections_export.md", debug_md="collections_debug.md"):
    session = Session()
    try:
        # проверка коллекций
        bad = validate_collections(session)
        if bad:
            print("Warning: обнаружены неизвестные card_type id в COLLECTIONS_IDS:")
            for col, ids in bad.items():
                print(f"  {col}: {ids}")

        # подготовка cardtype lookup (чтобы печатать имя карточки в debug)
        ct_all = {ct.id: f"{ct.first_name} {ct.last_name or ''}".strip() for ct in session.query(CardType).all()}

        user_map, user_cards = build_user_cards(session)
        total_cardtypes_count = session.query(CardType).count()

        # подготовка структуры результатов
        collection_results = {col: [] for col in COLLECTIONS_IDS.keys()}
        collection_debug = {col: [] for col in COLLECTIONS_IDS.keys()}

        for uid, cards_dict in user_cards.items():
            activated_ct_ids = set(cards_dict.keys())
            # общая последняя активация юзера
            last_activation_overall = max((d for d in cards_dict.values() if d is not None), default=None)
            user_has_all = len(activated_ct_ids) >= total_cardtypes_count

            for col_name, ct_ids in COLLECTIONS_IDS.items():
                ct_set = set(ct_ids)
                if user_has_all:
                    # если у юзера все карточки — считаем, что у него все коллекции
                    last_date = last_activation_overall
                    match_ids = ct_set & activated_ct_ids
                    if last_date and len(match_ids) >= MIN_MATCH_COUNT:
                        collection_results[col_name].append((user_map[uid], last_date))
                        collection_debug[col_name].append((user_map[uid], sorted(match_ids), 
                                                           {i: cards_dict.get(i) for i in match_ids}))
                else:
                    inter = activated_ct_ids.intersection(ct_set)
                    if len(inter) >= MIN_MATCH_COUNT:
                        # дата последней активации в этой коллекции
                        last_date = max((cards_dict[i] for i in inter if cards_dict.get(i)), default=None)
                        if last_date:
                            collection_results[col_name].append((user_map[uid], last_date))
                            collection_debug[col_name].append((user_map[uid], sorted(inter),
                                                               {i: cards_dict.get(i) for i in inter}))

        # сортировка
        for col in collection_results:
            collection_results[col].sort(key=lambda p: p[1], reverse=True)
            collection_debug[col].sort(key=lambda p: max((d for d in p[2].values() if d), default=datetime.min), reverse=True)

        # записываем основной экспорт
        with open(output_md, "w", encoding="utf-8") as f:
            f.write(f"# Экспорт коллекций — {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
            for col_name, entries in collection_results.items():
                f.write(f"## {col_name}\n\n")
                if not entries:
                    f.write("_Никто ещё не активировал карточки этой коллекции._\n\n")
                    continue
                for user, last_dt in entries:
                    dt_str = last_dt.strftime("%d.%m.%Y") if last_dt else "—"
                    username = f"@{user.username}" if user.username else f"{user.first_name or ''} {user.last_name or ''}".strip()
                    f.write(f"*{user.id}* {username} - {dt_str}\n")
                f.write("\n")

        # пишем детализованный debug файл
        with open(debug_md, "w", encoding="utf-8") as f:
            f.write(f"# Debug report — {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
            f.write(f"MIN_MATCH_COUNT = {MIN_MATCH_COUNT}\n\n")
            for col_name, entries in collection_debug.items():
                f.write(f"## {col_name}\n\n")
                if not entries:
                    f.write("_Нет совпадений._\n\n")
                    continue
                for user, match_ids, id_to_dt in entries:
                    username = f"@{user.username}" if user.username else f"{user.first_name or ''} {user.last_name or ''}".strip()
                    # строка с id:date и name
                    pairs = []
                    for cid in match_ids:
                        dt = id_to_dt.get(cid)
                        dt_s = dt.strftime("%d.%m.%Y %H:%M:%S") if dt else "—"
                        name = ct_all.get(cid, f"#{cid}")
                        pairs.append(f"{cid}({name})@{dt_s}")
                    f.write(f"*{user.id}* {username} - matched {len(match_ids)}: " + ", ".join(pairs) + "\n")
                f.write("\n")

        print("Экспорт завершён:", output_md)
        print("Debug report:", debug_md)
    finally:
        session.close()

if __name__ == "__main__":
    export()
