from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import psycopg2
import time
import random

# Укажите путь к chromedriver
chrome_driver_path = r"C:\Users\Ваграм\chromedriver.exe"

# Настройка Selenium для работы с браузером Chrome
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service)

# Параметры подключения к базе данных PostgreSQL
db_config = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "AKvagr3?",
    "port": "5432"
}

# Функция для сохранения данных в PostgreSQL
def save_to_postgres(data):
    try:
        # Подключение к базе данных
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        # SQL-запрос для вставки данных
        insert_query = """
            INSERT INTO auto.car_listings_2 (car_name, engine_volume, engine_power, fuel_type, transmission, body_type, drive_type, equipment, options, price_discounted, price, link, year, mileage_status, seller)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """

        # Вставка данных
        cursor.executemany(insert_query, data)
        connection.commit()

        print("Данные успешно добавлены в базу данных PostgreSQL")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Ошибка при подключении к PostgreSQL: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()

# Функция для парсинга страницы с объявлениями на auto.ru
def parse_auto_ru(url, num_pages):
    car_data = []
    is_captcha_passed = False

    for page in range(1, num_pages + 1):
        current_url = url + f"?page={page}"
        driver.get(current_url)

        if not is_captcha_passed:
            input("Пожалуйста, введите капчу и нажмите Enter...")  # Вводим капчу только один раз
            is_captcha_passed = True

        # Даем странице загрузиться
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, "ListingItem")))
        
        # Прокручиваем страницу вниз для загрузки всех объявлений (опционально)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(7, 15))  # Рандомная пауза от 7 до 15 секунд
        
        # Извлекаем HTML-код страницы
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')
        
        # Ищем все объявления на странице
        cars = soup.find_all('div', class_='ListingItem')

        for car in cars:
            tech_columns = car.find_all('div', class_='ListingItemTechSummaryDesktop__column')
            link_element = car.find('a', class_='ListingItemTitle__link')
            price_element = car.find('a', class_='Link ListingItemPrice__link')
            price_element2 = car.find('div', class_='ListingItemPrice ListingItem__price ListingItem__price_second')
            year_element = car.find('div', class_='ListingItem__year')  # Год автомобиля
            km_age_element = car.find('div', class_='ListingItem__kmAge')  # Пробег или статус (Новый)
            seller_element = car.find('a', class_='ListingItem__salonName')  # Продавец

            if len(tech_columns) >= 1 and link_element:
                # Первый столбец с характеристиками
                tech_cells_1 = tech_columns[0].find_all('div', class_='ListingItemTechSummaryDesktop__cell')
                
                # Второй столбец с характеристиками (если он существует)
                tech_cells_2 = tech_columns[1].find_all('div', class_='ListingItemTechSummaryDesktop__cell') if len(tech_columns) > 1 else []

                # Обрабатываем первый столбец
                engine_info = tech_cells_1[0].text.strip().replace('\u2009', ' ').replace('\xa0', ' ') if len(tech_cells_1) > 0 else ''
                engine_parts = engine_info.split(' / ')

                engine_volume = engine_parts[0] if len(engine_parts) > 0 else ''
                engine_power = engine_parts[1] if len(engine_parts) > 1 else ''
                fuel_type = engine_parts[2] if len(engine_parts) > 2 else ''

                transmission = tech_cells_1[1].text.strip() if len(tech_cells_1) > 1 else ''
                body_type = tech_cells_1[2].text.strip() if len(tech_cells_1) > 2 else ''

                # Обрабатываем второй столбец (если он существует)
                drive_type = tech_cells_2[0].text.strip() if len(tech_cells_2) > 0 else ''
                trim = tech_cells_2[1].text.strip() if len(tech_cells_2) > 1 else ''  # Оставляем пустое значение, если элемента нет
                options = tech_cells_2[2].text.strip() if len(tech_cells_2) > 2 else ''  # Оставляем пустое значение, если элемента нет

                # Название автомобиля
                car_name = link_element.text.strip()

                # Ссылка и цена
                link = link_element.get('href')
                price = price_element.find('span').text.strip() if price_element else ''
                price2 = price_element2.find('span').text.strip() if price_element2 else ''

                # Добавляем новые данные
                year = year_element.text.strip() if year_element else ''  # Год выпуска
                km_age = km_age_element.text.strip() if km_age_element else ''  # Пробег или статус
                seller = seller_element.text.strip() if seller_element else ''  # Продавец

                # Добавляем данные в список
                car_data.append([car_name, engine_volume, engine_power, fuel_type, transmission, body_type, drive_type, trim, options, price, price2, link, year, km_age, seller])
            else:
                print("Элемент не найден или данных недостаточно, пропускаем...")

        print(f"Страница {page} успешно обработана")

    return car_data

# Основная функция
def main():
    url = "https://auto.ru/moskovskaya_oblast/cars/jetour/all/"
    num_pages = 53 # Количество страниц для парсинга
    car_listings = parse_auto_ru(url, num_pages)

    if car_listings:
        save_to_postgres(car_listings)  # Сохраняем данные напрямую в PostgreSQL

if __name__ == "__main__":
    main()

# После завершения работы не забываем закрыть браузер

driver.quit()
