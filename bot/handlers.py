from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import ContextTypes
import bot.db_requests as rq
import os

TOKEN = os.getenv("TOKEN")


async def get_avatar_url(user_id, context):
    photos = await context.bot.get_user_profile_photos(user_id)
    if photos.total_count > 0:
        file_id = photos.photos[0][0].file_id
        file = await context.bot.get_file(file_id)

        if file.file_path.startswith("https://"):
            return file.file_path
        else:
            return f"https://api.telegram.org/file/bot{os.getenv('TOKEN')}/{file.file_path}"
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    avatar_url = await get_avatar_url(user.id, context)

    rq.add_user(user.id, user.username, avatar_url)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Открыть Web App", web_app=WebAppInfo(url="https://cardspb4.ru"))]
    ])

    text = (
        "Привет! На связи <b>Балдёжный Четвёртый ✨</b>\n\n"
        "Мы запустили крутой ивент – <b>\"Карточки активистов\"</b>, "
        "который позволит тебе узнать всех активистов <b>балдёжного профбюро</b>, "
        "а также выиграть крутые призы!\n\n"
        "<i>Что нужно делать?</i>\n\n"

        "<b>1.</b> Собирай карточки активистов <i>на мероприятиях Профбюро 4 института</i>\n"
        "(В разделе \"Где получить?\" ты увидишь все места, где возможно их собрать)\n\n"

        "<b>2.</b> После входа в Mini-App введи <b>уникальный код</b>, написанный на обратной стороне твоей карточки!\n\n"
        "🔹Каждая карточка уникальна, и после ввода кода она останется только у тебя в профиле\n"
        "🔹Некоторые карточки после их активации дают маленький приз (тут всё зависит от везения😊)\n\n"

        "<b>3.</b> В разделе \"Коллекция\" ты можешь просмотреть всех открытых активистов, "
        "а также тех, кого тебе ещё предстоит собрать😉\n\n"

        "<b>4.</b> Для получения 🎁<b>САМОГО БАЛДЁЖНОГО</b>🎁 приза от актива нашего профбюро "
        "ты должен собрать <b>все карточки одной коллекции</b> "
        "(кроме коллекций \"Председатель\" и \"Креативно-ревизионный отдел\")\n\n"

        "<b>5.</b> Физическая карточка должна оставаться у тебя в <b>целости и сохранности</b>, "
        "чтобы ты мог получить приз!\n\n"

        "<i>Заходи в Mini-App по кнопке ниже и собери всех активистов! 😎</i>"
    )

    photo_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "startpic.png")

    with open(photo_path, "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
