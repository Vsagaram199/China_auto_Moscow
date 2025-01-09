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
            INSERT INTO auto.spares_drom(description,price)
            VALUES (%s, %s);
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

    # Функция для парсинга страницы с объявлениями на drom.ru
def parse_dynamic_drom_page(url):
    driver.get(url)
    time.sleep(5)

    is_captcha_passed = False  # Флаг для отслеживания капчи
    spare_data = []  # Список для хранения извлеченных данных

    for scroll_count in range(25):  # Количество прокруток (можно настроить)
        print(f"Прокрутка страницы: {scroll_count + 1}")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(4,11))  # Ждем, чтобы элементы успели подгрузиться

        if not is_captcha_passed:
            input("Пожалуйста, введите капчу и нажмите Enter...")  # Вводим капчу только один раз
            is_captcha_passed = True

        # Даем странице загрузиться
        WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, "//tr[contains(@class, 'bull-list-item-js') and contains(@class, '-exact')]")))
        
        # Извлекаем HTML-код страницы
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')

        spares = soup.find_all('tr', {'class': 'bull-list-item-js'})
        print(f"Найдено объявлений: {len(spares)}")
        for spare in spares:
            description_element = spare.find('div', class_='bull-item__subject-container')
            price_element = spare.find('div', class_='price-block__price')
            if description_element and price_element:
                try:
                    link_element = description_element.find('a', class_='bulletinLink')
                    description = link_element.text.strip() if link_element else ''
                    price = price_element.get_text(strip=True).replace('₽', '').strip()
                    spare_data.append((description, price))
                except Exception as e:
                    print(f"Ошибка при парсинге описания: {e}")
            else:
                print("Элемент не найден или данных недостаточно, пропускаем...")

    return spare_data

# Основная функция
def main():
    url = "https://baza.drom.ru/moskovskaya-obl/sell_spare_parts/model/jaecoo/"
    start_time = time.time()  # Запуск таймера
    drom_spare = parse_dynamic_drom_page(url)

    print(f"Общее время выполнения: {time.time() - start_time:.2f} секунд")

    if drom_spare:
        save_to_postgres(drom_spare)  # Сохраняем данные напрямую в PostgreSQL

if __name__ == "__main__":
    main()

# После завершения работы не забываем закрыть браузер

driver.quit()


    