from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import psycopg2
import time
import random
import re

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
            INSERT INTO telegrambot.changan_auto_ru (car_name, year,mileage_status,link,price,car_volume,car_power,body_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
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

# **Функция для определения количества страниц**
def get_total_pages(url):
    driver.get(url)

    try:
        # Ждем появления блока пагинации
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ListingPagination__pages"))
        )
        
        # Ищем блок пагинации
        pagination_block = driver.find_element(By.CLASS_NAME, "ListingPagination__pages")
        # Ищем все элементы с классом Button__text внутри блока пагинации
        pagination_numbers = pagination_block.find_elements(By.CLASS_NAME, "Button__text")
        
        # Сохраняем номера страниц из текста элементов
        page_numbers = []
        for number in pagination_numbers:
            try:
                page_text = number.text.strip()
                if page_text.isdigit():  # Убедимся, что это число
                    page_numbers.append(int(page_text))
            except Exception as e:
                print(f"Ошибка при обработке номера страницы: {e}")

        # Определяем максимальный номер страницы
        if page_numbers:
            total_pages = max(page_numbers)
            print(f"Обнаружено страниц: {total_pages}")
            return total_pages

    except Exception as e:
        print(f"Ошибка при определении количества страниц: {e}")

    # Если блок не найден, возвращаем 1
    print("Блок пагинации не найден или страницы не определены. Возвращаю 1.")
    return 1
# Функция для парсинга страницы с объявлениями на auto.ru
def parse_auto_ru(url):
    car_data = []
    is_captcha_passed = False

    # **Определяем количество страниц**
    num_pages = get_total_pages(url)
    print(f"Обнаружено страниц: {num_pages}")

    for page in range(1, num_pages + 1):
        current_url = url + f"?page={page}"
        driver.get(current_url)

        if not is_captcha_passed:
            input("Пожалуйста, введите капчу и нажмите Enter...")  # Вводим капчу только один раз
            is_captcha_passed = True

        # Даем странице загрузиться
        WebDriverWait(driver, 45).until(EC.presence_of_element_located((By.CLASS_NAME, "ListingItem")))
        
        # Прокручиваем страницу вниз для загрузки всех объявлений (опционально)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(7, 12))  # Рандомная пауза от 7 до 15 секунд
        
        # Извлекаем HTML-код страницы
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')
        
        # Ищем все объявления на странице
        cars = soup.find_all('div', class_='ListingItem')

        for car in cars:
            try:
                 # Название автомобиля
                link_element = car.find('a', class_='ListingItemTitle__link')
                car_name = link_element.text.strip() if link_element else None

                # Ссылка на объявление
                link = link_element.get('href') if link_element else None

                # Цена
                price_element = car.find('a', class_='Link ListingItemPrice__link')
                if price_element:
                    price_text=price_element.find('span').text.strip()
                    price_text = re.sub(r'[^\d]', '', price_text)  # Убираем символы, кроме цифр
                    price=int(price_text) if price_text else 0  # Преобразуем в число
                else:
                    price=0

                # Год выпуска
                year_element = car.find('div', class_='ListingItem__year')
                year = year_element.text.strip() if year_element else None

                # Пробег или статус (Новый)
                km_age_element = car.find('div', class_='ListingItem__kmAge')
                km_age = km_age_element.text.strip() if km_age_element else None

                #Технические элементы
                tech_summary_element=car.find('div', class_='ListingItemTechSummaryDesktop__cell')
                tech_summary_text=tech_summary_element.text.strip()
                tech_parts=tech_summary_text.split('/')
                engine_volume=tech_parts[0].strip() if len(tech_parts) > 0 else None
                engine_power=tech_parts[1].replace('л.с.', '').strip() if len(tech_parts) > 1 else None
                body_type = tech_parts[-1].strip() if len(tech_parts) > 2 else ''

                # Проверяем, что данные корректно собраны
                if all([car_name, link, year, km_age, price,engine_volume,engine_power,body_type]):
                    # Добавляем данные в список
                    car_data.append([car_name, year, km_age, link, price,engine_volume,engine_power,body_type])
                else:
                    print(f"Данных недостаточно для одного из объявлений. Пропускаем...")
            except Exception as e:
                print(f"Ошибка при обработке объявления: {e}")

        print(f"Страница {page} успешно обработана")

    return car_data

# Основная функция
def main():
    url = "https://auto.ru/moskovskaya_oblast/cars/changan/all/"
    car_listings = parse_auto_ru(url)

    if car_listings:
        save_to_postgres(car_listings)  # Сохраняем данные напрямую в PostgreSQL

if __name__ == "__main__":
    main()

# После завершения работы не забываем закрыть браузер

driver.quit()
