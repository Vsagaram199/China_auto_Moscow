from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv

# Загружаем данные из .env файла
load_dotenv("d:/gitprojects/Token.env")

# Получаем токен и Telegram ID из .env
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MY_TELEGRAM_ID = int(os.getenv("MY_TELEGRAM_ID"))

# Флаг для остановки бота
is_bot_active = True

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_active
    if update.effective_user.id == MY_TELEGRAM_ID:
        is_bot_active = True  # Активируем бота
        await update.message.reply_text("Привет, Ваграм! Это ваш личный бот.")
    else:
        await update.message.reply_text("Извините, этот бот не предназначен для вас.")

# Обработчик команды /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_active
    if update.effective_user.id == MY_TELEGRAM_ID:
        is_bot_active = False
        await update.message.reply_text("Бот остановлен. Он больше не будет отвечать.")
    else:
        await update.message.reply_text("Извините, этот бот не предназначен для вас.")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_active
    if is_bot_active:
        if update.effective_user.id == MY_TELEGRAM_ID:
            await update.message.reply_text(f"Вы написали: {update.message.text}")
        else:
            await update.message.reply_text("Вы не авторизованы для использования этого бота.")
    else:
        await update.message.reply_text("Бот остановлен и больше не отвечает.")

# Основная функция для запуска бота
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()