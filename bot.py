import random
import sqlite3
import datetime
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes

# Подключаемся к базе данных
conn = sqlite3.connect("messages.db", check_same_thread=False)
cursor = conn.cursor()

# Создаём таблицу для хранения сообщений
cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_type TEXT,
        content TEXT,
        timestamp TIMESTAMP
    )
""")
conn.commit()

# Функция для сохранения сообщения в базу данных
def save_message(message_type, content):
    cursor.execute("INSERT INTO messages (message_type, content, timestamp) VALUES (?, ?, ?)",
                   (message_type, content, datetime.datetime.now()))
    conn.commit()

# Обработчик для получения сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text:
        save_message("text", update.message.text)
    elif update.message.sticker:
        save_message("sticker", update.message.sticker.file_id)
    elif update.message.animation:  # Это для GIF
        save_message("animation", update.message.animation.file_id)

# Команда для случайной отправки сообщения
async def send_random_message(context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT * FROM messages ORDER BY RANDOM() LIMIT 2")
    messages = cursor.fetchall()

    # Если в базе данных есть сообщения
    if messages:
        combined_message = " ".join([msg[2] for msg in messages if msg[1] == "text"])
        chat_id = context.job.chat_id

        # Отправляем комбинированное текстовое сообщение, если оно есть
        if combined_message:
            await context.bot.send_message(chat_id=chat_id, text=combined_message)
        
        # Отправляем случайный стикер или GIF
        for msg in messages:
            if msg[1] == "sticker":
                await context.bot.send_sticker(chat_id=chat_id, sticker=msg[2])
            elif msg[1] == "animation":
                await context.bot.send_animation(chat_id=chat_id, animation=msg[2])

# Команда для запуска отправки случайных сообщений
async def start_sending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.job_queue.run_repeating(send_random_message, interval=random.randint(1800, 7200), context=chat_id, name=str(chat_id))
    await update.message.reply_text("Бот будет отправлять случайные сообщения!")

# Основная функция для запуска бота
def main():
    app = Application.builder().token("7904602572:AAETfxHCNQfzYLwQuBlO5OltGS0zsewG0zI").build()

    # Добавляем обработчики сообщений и команд
    app.add_handler(MessageHandler(filters.TEXT | filters.STICKER | filters.ANIMATION, handle_message))
    app.add_handler(CommandHandler("start_sending", start_sending))

    app.run_polling()

if name == "main":
    main()