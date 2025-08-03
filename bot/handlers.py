from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import ContextTypes
from . import requests as rq
import os

TOKEN = os.getenv("TOKEN")


async def get_avatar_url(user_id, context):
    photos = await context.bot.get_user_profile_photos(user_id)
    if photos.total_count > 0:
        file_id = photos.photos[0][0].file_id
        file = await context.bot.get_file(file_id)
        return file.file_path
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    avatar_path = await get_avatar_url(user.id, context)
    avatar_url = f"https://api.telegram.org/file/bot{TOKEN}/{avatar_path}" if avatar_path else None

    rq.add_user(user.username, avatar_url)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Открыть Web App", web_app=WebAppInfo(url="https://cardspb4.ru"))]
    ])
    await update.message.reply_text("Нажми кнопку, чтобы открыть приложение:", reply_markup=keyboard)
