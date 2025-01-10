from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackContext
from telegram.ext import CommandHandler
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
is_bot_active = False
current_page = 1

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

# Главная клавиатура
def main_menu_keyboard():
    keyboard = [
        [KeyboardButton("Старт"), KeyboardButton("Стоп")],
        [KeyboardButton("Фильтр"), KeyboardButton("Следующая страница")],
        [KeyboardButton("Помощь")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Подменю фильтров
def filter_menu_keyboard():
    keyboard = [
        [KeyboardButton("Год"), KeyboardButton("Объем")],
        [KeyboardButton("Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Обработчик кнопки "Старт"
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_active, current_page
    if update.effective_user.id == MY_TELEGRAM_ID:
        is_bot_active = True
        current_page = 1
        await update.message.reply_text(
            "Бот активирован. Используйте кнопки для удобства:",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text("Извините, этот бот не предназначен для вас.")

# Обработчик кнопки "Стоп"
async def handle_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_active
    if update.effective_user.id == MY_TELEGRAM_ID:
        is_bot_active = False
        await update.message.reply_text(
            "Бот остановлен. Нажмите \"Старт\" для активации.",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text("Извините, этот бот не предназначен для вас.")

# Обработчик кнопки "Фильтр"
async def handle_filter(update: Update, context: CallbackContext):
    if not is_bot_active:
        await update.message.reply_text("Бот остановлен. Активируйте его кнопкой \"Старт\".")
        return
    await update.message.reply_text(
        "Выберите критерий фильтрации:",
        reply_markup=filter_menu_keyboard()
    )

# Обработчик кнопки "Год"
async def handle_year(update: Update, context: CallbackContext):
    if not is_bot_active:
        await update.message.reply_text("Бот остановлен. Активируйте его кнопкой \"Старт\".")
        return
    await update.message.reply_text("Введите год для поиска автомобилей:")
    context.user_data['filter_mode'] = 'year'

# Обработчик кнопки "Объем"
async def handle_volume(update: Update, context: CallbackContext):
    if not is_bot_active:
        await update.message.reply_text("Бот остановлен. Активируйте его кнопкой \"Старт\".")
        return
    await update.message.reply_text("Введите объем двигателя для поиска автомобилей:")
    context.user_data['filter_mode'] = 'volume'

# Обработчик кнопки "Назад"
async def handle_back(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Возвращаемся в главное меню.",
        reply_markup=main_menu_keyboard()
    )

# Запрос данных из базы
def get_filtered_cars(car_volume=None, year=None, page=1):
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
            query += " AND TRIM(car_volume) = %s"  # Точное совпадение с учетом удаления лишних пробелов
            params.append(car_volume)

        if year:
            query += " AND year = %s"
            params.append(year)

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

# Обработчик кнопки "Следующая страница"
async def handle_next_page(update: Update, context: CallbackContext):
    global current_page
    if not is_bot_active:
        await update.message.reply_text("Бот остановлен. Активируйте его кнопкой \"Старт\".")
        return

    current_page += 1
    cars = get_filtered_cars(page=current_page)

    if not cars:
        await update.message.reply_text("Больше нет данных.")
        current_page -= 1
        return

    response = "\n\n".join([
        f"Модель: {car[0]}\nГод: {car[1]}\nПробег: {car[2]} км\nЦена: {car[3]}\n"
        f"Объём двигателя: {car[4]}\nМощность: {car[5]} л.с.\nСсылка: {car[6]}"
        for car in cars
    ])
    await update.message.reply_text(response)

# Обработчик текстового ввода (год или объем)
async def handle_text_input(update: Update, context: CallbackContext):
    if not is_bot_active:
        await update.message.reply_text("Бот остановлен. Активируйте его кнопкой \"Старт\".")
        return

    user_input = update.message.text.strip()
    filter_mode = context.user_data.get('filter_mode')

    try:
        if filter_mode == 'year' and user_input.isdigit():
            year = int(user_input)
            cars = get_filtered_cars(year=year)
        elif filter_mode == 'volume':
            # Добавляем " л" к объему, если пользователь забыл указать
            if not user_input.endswith(" л"):
                user_input = user_input.strip() + " л"

            car_volume = user_input
            cars = get_filtered_cars(car_volume=car_volume)
        else:
            await update.message.reply_text("Некорректный ввод. Попробуйте снова.")
            return

        if not cars:
            await update.message.reply_text("Нет данных по заданным параметрам.")
            return

        response = "\n\n".join([
            f"Модель: {car[0]}\nГод: {car[1]}\nПробег: {car[2]} км\nЦена: {car[3]}\n"
            f"Объём двигателя: {car[4]}\nМощность: {car[5]} л.с.\nСсылка: {car[6]}"
            for car in cars
        ])
        await update.message.reply_text(response, reply_markup=main_menu_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Ошибка обработки данных: {e}")

# Основная функция
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(MessageHandler(filters.Regex("^(Старт)$"), handle_start))
    application.add_handler(MessageHandler(filters.Regex("^(Стоп)$"), handle_stop))
    application.add_handler(MessageHandler(filters.Regex("^(Фильтр)$"), handle_filter))
    application.add_handler(MessageHandler(filters.Regex("^(Год)$"), handle_year))
    application.add_handler(MessageHandler(filters.Regex("^(Объем)$"), handle_volume))
    application.add_handler(MessageHandler(filters.Regex("^(Назад)$"), handle_back))
    application.add_handler(MessageHandler(filters.Regex("^(Следующая страница)$"), handle_next_page))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()


