import logging
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)
from config import TELEGRAM_BOT_TOKEN, RENDER_EXTERNAL_URL
from generator import generate_coloring_image
from storage import log_user_choice, log_user_feedback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

flask_app = Flask(__name__)
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

user_sessions = {}  # зберігає тимчасові вибори користувача

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я допоможу створити розмальовки для вашої дитини 🎨\nНатисніть, щоб почати.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Почати", callback_data="start_flow")]
        ])
    )

# Callback обробник вибору параметрів
# (... реалізація кроків: вік → тематика → кількість → формат → генерація ...)

# Генерація зображення та надсилання
# (... generate_coloring_image, оцінки, логування ...)

# Flask endpoint для webhook
@flask_app.post("/")
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "OK"

telegram_app.add_handler(CommandHandler("start", start))
# (... інші CallbackQueryHandler для кроків вибору ...)

async def run():
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()

if __name__ == "__main__":
    asyncio.run(run())
