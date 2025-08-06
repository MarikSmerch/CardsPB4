from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from bot.db import create_all_tables
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")


if __name__ == '__main__':
    from handlers import start
    create_all_tables()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
