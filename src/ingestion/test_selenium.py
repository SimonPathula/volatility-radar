import time 
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

url = "https://www.forexfactory.com/calendar?week=jan3.2022" 
driver = webdriver.Chrome()
driver.get(url)

wait = WebDriverWait(driver, 15)
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "calendar__row")))

# scroll slowly in steps
for i in range(1, 10):
    driver.execute_script(f"window.scrollTo(0, {i * 500});")
    time.sleep(0.5)

time.sleep(2)

page_source = driver.page_source

target_currencies = ["EUR", "GBP", "USD", "JPY"]

soup = BeautifulSoup(page_source, "html.parser")
rows  = soup.find_all("tr", class_ = "calendar__row")

count = 0

current_date = ""

for row in rows:

    currency = row.find("td", class_ = "calendar__currency")

    if currency:
        currency_text = currency.get_text(strip=True)

        if currency_text in target_currencies:
            time = row.find('td', class_ = "calendar__time")
            event = row.find('td', class_ = "calendar__event")
            actual = row.find('td', class_ = "calendar__actual")
            forecast = row.find('td', class_ = "calendar__forecast")
            previous = row.find('td', class_ = "calendar__previous")

            actual_text = actual.get_text(strip=True) if actual else ''
            forecast_text = forecast.get_text(strip=True) if forecast else ''
            previous_text = previous.get_text(strip=True) if previous else ''

            if not actual_text and not forecast_text and not previous_text:
                continue

            print(
                currency_text,
                time.get_text(strip=True) if time else '',
                event.get_text(strip=True) if event else '',
                actual_text,
                forecast_text,
                previous_text
            )
            count += 1
print(count)
driver.close()

