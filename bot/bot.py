from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from db import create_all_tables
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Открыть Web App", web_app=WebAppInfo(url="https://cardspb4.ru"))]
    ])
    await update.message.reply_text("Нажми кнопку, чтобы открыть приложение:", reply_markup=keyboard)


if __name__ == '__main__':
    # Создание всех таблиц при первом запуске
    create_all_tables()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

