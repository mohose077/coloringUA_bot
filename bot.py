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

# Обробка вибору параметрів
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_sessions:
        user_sessions[user_id] = {}

    data = query.data

    if data == "start_flow":
        await query.edit_message_text(
            "Скільки років дитині?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("2-3 роки", callback_data="age_2-3")],
                [InlineKeyboardButton("4 роки", callback_data="age_4")],
                [InlineKeyboardButton("5 років", callback_data="age_5")],
                [InlineKeyboardButton("6 років", callback_data="age_6")]
            ])
        )

    elif data.startswith("age_"):
        user_sessions[user_id]["age"] = data.replace("age_", "")
        await query.edit_message_text(
            "Оберіть тематику розмальовок:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Дісней", callback_data="theme_Дісней")],
                [InlineKeyboardButton("Тварини", callback_data="theme_Тварини")],
                [InlineKeyboardButton("Машинки", callback_data="theme_Машинки")],
                [InlineKeyboardButton("Динозаври", callback_data="theme_Динозаври")],
                [InlineKeyboardButton("Казкові", callback_data="theme_Казкові")],
                [InlineKeyboardButton("Їжа", callback_data="theme_Їжа")]
            ])
        )

    elif data.startswith("theme_"):
        user_sessions[user_id]["theme"] = data.replace("theme_", "")
        await query.edit_message_text(
            "Скільки зображень потрібно?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("1", callback_data="count_1")],
                [InlineKeyboardButton("3", callback_data="count_3")],
                [InlineKeyboardButton("5", callback_data="count_5")],
                [InlineKeyboardButton("10", callback_data="count_10")]
            ])
        )

    elif data.startswith("count_"):
        user_sessions[user_id]["count"] = int(data.replace("count_", ""))
        await query.edit_message_text(
            "Який формат аркуша?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("A4", callback_data="format_A4")],
                [InlineKeyboardButton("A5", callback_data="format_A5")]
            ])
        )

    elif data.startswith("format_"):
        user_sessions[user_id]["format"] = data.replace("format_", "")
        await query.edit_message_text("Генерую зображення... 🎨")

        # Збереження вибору
        log_user_choice(user_id, user_sessions[user_id])

        # Генерація зображень
        count = user_sessions[user_id]["count"]
        for i in range(count):
            image_url = generate_coloring_image(
                user_sessions[user_id]["age"],
                user_sessions[user_id]["theme"],
                user_sessions[user_id]["format"]
            )
            await context.bot.send_photo(
                chat_id=user_id,
                photo=image_url,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("👍", callback_data=f"like_{image_url}"),
                        InlineKeyboardButton("👎", callback_data=f"dislike_{image_url}")
                    ]
                ])
            )

        await context.bot.send_message(chat_id=user_id, text="Дякуємо за користування ботом! 💛💙")

    elif data.startswith("like_") or data.startswith("dislike_"):
        image_url = data.split("_", 1)[1]
        feedback = "like" if data.startswith("like_") else "dislike"
        log_user_feedback(user_id, image_url, feedback)
        await query.answer("Дякуємо за оцінку!")

# Flask endpoint для webhook
@flask_app.post("/")
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "OK"

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(handle_callback))

async def run():
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()

if __name__ == "__main__":
    asyncio.run(run())
