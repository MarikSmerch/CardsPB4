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
    await update.message.reply_text("Нажми кнопку, чтобы открыть приложение:", reply_markup=keyboard)

