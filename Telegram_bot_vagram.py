from telegram import Update
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

# Подключение к PostgreSQL
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

# Флаг для остановки бота
is_bot_active = True

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_active
    if update.effective_user.id == MY_TELEGRAM_ID:
        is_bot_active = True
        await update.message.reply_text("Привет, Ваграм! Бот активирован.")
    else:
        await update.message.reply_text("Извините, этот бот не предназначен для вас.")

# Обработчик команды /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_active
    if update.effective_user.id == MY_TELEGRAM_ID:
        is_bot_active = False
        await update.message.reply_text("Бот остановлен.")
    else:
        await update.message.reply_text("Извините, этот бот не предназначен для вас.")

# Функция для получения данных из базы с фильтром
def get_filtered_cars(car_name=None,year=None):
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

        if car_name:
            query += " AND car_name ILIKE %s"
            params.append(f"%{car_name}%")  # Добавляем подстановочные знаки для частичного поиска

        if year:
            query += " AND year = %s"
            params.append(year)


        query += " LIMIT 10"

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

    # Парсим аргументы команды
    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text("Пожалуйста, укажите модель и год выпуска, например: /filter Changan 2024")
        return

    car_name = args[0]
    year = args[1]


    cars = get_filtered_cars(car_name,year)
    if not cars:
        await update.message.reply_text("Нет данных по заданным фильтрам.")
        return

    response = "\n\n".join([
        f"Модель: {car[0]}\nГод: {car[1]}\nПробег: {car[2]} км\nЦена: {car[3]}\nОбъём двигателя: {car[4]} л\nМощность: {car[5]} л.с.\nСсылка: {car[6]}"
        for car in cars
    ])
    await update.message.reply_text(response)

# Основная функция для запуска бота
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("filter", filter_cars))

    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()