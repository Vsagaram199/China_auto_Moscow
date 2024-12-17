from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
import os
from dotenv import load_dotenv
import psycopg2

# Загружаем данные из .env файла
load_dotenv("d:/gitprojects/Token.env")

# Получаем токен и данные для подключения к базе
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MY_TELEGRAM_ID = int(os.getenv("MY_TELEGRAM_ID"))

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Глобальные переменные
is_bot_active = True

# Функция подключения к базе данных
def get_db_connection():
    try:
        connection = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return connection
    except psycopg2.Error as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None

# Главная клавиатура с кнопками
def main_menu_keyboard():
    keyboard = [
        [KeyboardButton("Старт"), KeyboardButton("Стоп")],
        [KeyboardButton("/filter Changan 2024"), KeyboardButton("/filter car_volume=2.0")],
        [KeyboardButton("Помощь")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_active
    if update.effective_user.id == MY_TELEGRAM_ID:
        is_bot_active = True
        await update.message.reply_text(
            "Привет, Ваграм! Бот активирован.\nИспользуйте кнопки для удобства:",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text("Извините, этот бот не предназначен для вас.")

# Обработчик команды /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_active
    if update.effective_user.id == MY_TELEGRAM_ID:
        is_bot_active = False
        await update.message.reply_text(
            "Бот остановлен. Нажмите /start для активации.",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text("Извините, этот бот не предназначен для вас.")

# Запрос данных из базы
def get_filtered_cars(car_volume=None, year=None, car_name=None, page=1):
    connection = get_db_connection()
    if connection is None:
        return []

    try:
        query = """
            SELECT car_name, year, mileage_status, price, car_volume, car_power, link
            FROM telegrambot.changan_auto_ru
            WHERE 1=1
        """
        params = []

        if car_volume:
            query += " AND car_volume ILIKE %s"
            params.append(f"%{car_volume}%")

        if year:
            query += " AND year = %s"
            params.append(year)

        if car_name:
            query += " AND car_name ILIKE %s"
            params.append(f"%{car_name}%")

        # Пагинация
        limit = 10
        offset = (page - 1) * limit
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with connection.cursor() as cursor:
            cursor.execute(query, tuple(params))
            cars = cursor.fetchall()

        return cars
    except psycopg2.Error as e:
        print(f"Ошибка выполнения запроса: {e}")
        return []
    finally:
        connection.close()

# Обработчик команды /filter
async def filter_cars(update: Update, context: CallbackContext):
    if not is_bot_active:
        await update.message.reply_text("Бот остановлен. Активируйте его командой /start.")
        return

    if update.effective_user.id != MY_TELEGRAM_ID:
        await update.message.reply_text("Вы не авторизованы для использования этого бота.")
        return

    # Разбор аргументов команды
    args = context.args
    car_name, year, car_volume = None, None, None

    for arg in args:
        if arg.startswith("car_volume="):
            car_volume = arg.split("=")[1]
        elif arg.startswith("year="):
            year = arg.split("=")[1]
        else:
            car_name = arg

    cars = get_filtered_cars(car_volume, year, car_name)
    if not cars:
        await update.message.reply_text("Нет данных по заданным фильтрам.")
        return

    response = "\n\n".join([
        f"Модель: {car[0]}\nГод: {car[1]}\nПробег: {car[2]} км\nЦена: {car[3]}\n"
        f"Объём двигателя: {car[4]}\nМощность: {car[5]} л.с.\nСсылка: {car[6]}"
        for car in cars
    ])
    await update.message.reply_text(response)

# Обработчик случайных сообщений
async def unknown_message(update: Update, context: CallbackContext):
    await update.message.reply_text("Я не понимаю эту команду. Попробуйте воспользоваться кнопками.")

# Основная функция
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("filter", filter_cars))

    # Обработчик неизвестных сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()