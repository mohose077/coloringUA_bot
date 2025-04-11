# bot.py
import os
import logging
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
)
from config import TELEGRAM_BOT_TOKEN, RENDER_EXTERNAL_URL
from generator import generate_coloring_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

flask_app = Flask(__name__)
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привіт! Це бот, що створює розмальовки за обраними критеріями 🖍️\n\n"
        "1. Обери вік дитини\n"
        "2. Обери тему\n"
        "3. Вкажи кількість та формат\n"
        "4. Отримай розмальовки!\n\n"
        "⬇️ Обери вік:"
    )
    keyboard = [["2-3 роки", "4 роки"], ["5 років", "6 років"]]
    await update.message.reply_text("Вік дитини:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))

# Вік
async def handle_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    keyboard = [["Дісней", "Тварини"], ["Машинки", "Динозаври"], ["Казкові", "Їжа"]]
    await update.message.reply_text("⬆️ Обери тему:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))

# Тема
async def handle_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["topic"] = update.message.text
    keyboard = [["1", "3", "5"], ["10"]]
    await update.message.reply_text("🔢 Обери кількість зображень:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))

# Кількість
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["amount"] = update.message.text
    keyboard = [["A4", "A5"]]
    await update.message.reply_text("🗜️ Обери формат:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))

# Формат
async def handle_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["format"] = update.message.text
    age = context.user_data.get("age")
    topic = context.user_data.get("topic")
    amount = int(context.user_data.get("amount"))
    user_id = update.effective_chat.id

    await update.message.reply_text("🔧 Генеруємо розмальовки...")

    for i in range(amount):
        prompt = f"{topic} for children {age}"
        image_url = generate_coloring_image(prompt)
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👍 Подобається", callback_data=f"like|{image_url}"),
                InlineKeyboardButton("👎 Не подобається", callback_data=f"dislike|{image_url}")
            ]
        ])

        try:
            await context.bot.send_photo(chat_id=user_id, photo=image_url, caption=f"🖼 Розмальовка {i+1}/{amount}", reply_markup=keyboard)
        except Exception as e:
            await context.bot.send_message(chat_id=user_id, text="❌ Не вдалося надіслати зображення.")
            logger.error(f"Помилка надсилання зображення: {e}")

    await update.message.reply_text("✅ Усі розмальовки надіслані! Дякуємо за оцінки!")

# Оцінка
async def handle_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, image_url = query.data.split("|")
    await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ Ви оцінили: {'👍' if action == 'like' else '👎'}")

# Обробники
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.Regex("^(2-3 роки|4 роки|5 років|6 років)$"), handle_age))
telegram_app.add_handler(MessageHandler(filters.Regex("^(Дісней|Тварини|Машинки|Динозаври|Казкові|Їжа)$"), handle_topic))
telegram_app.add_handler(MessageHandler(filters.Regex("^(1|3|5|10)$"), handle_amount))
telegram_app.add_handler(MessageHandler(filters.Regex("^(A4|A5)$"), handle_format))
telegram_app.add_handler(CallbackQueryHandler(handle_rating))

# Flask маршрут
@flask_app.route('/')
def home():
    return '✅ Бот працює'

@flask_app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return 'OK', 200

if __name__ == "__main__":
    import asyncio
    asyncio.run(telegram_app.bot.delete_webhook(drop_pending_updates=True))
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        asyncio.run(telegram_app.bot.set_webhook(url=webhook_url))
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)
