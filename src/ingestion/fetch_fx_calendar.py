from distro import version
from random import random
import time
import random
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

target_currencies = ["EUR", "USD", "GBP", "JPY"]

result = []

def weekly_data_scraped(date):

    #give the url to the webdriver and open in chrome
    # driver = webdriver.Chrome()
    url = f"https://www.forexfactory.com/calendar?week={date}"
    driver.get(url)

    #wait for the webpage to load up
    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "calendar__row")))

    # scroll slowly in steps
    for i in range(1, 20):
        driver.execute_script(f"window.scrollTo(0, {i * 250});")
        time.sleep(0.3)

    time.sleep(1)

    page_source = driver.page_source

    soup = BeautifulSoup(page_source, "html.parser")

    #rows in the particular week
    rows = soup.find_all("tr", class_ = "calendar__row")

    for row in rows:
        date_cell = row.find("td", class_ = "calendar__date")

        if date_cell:
            current_date = date_cell.get_text(strip=True, separator= " ")

        currency_handle = row.find("td", class_ = "calendar__currency")
        
        if currency_handle:
            currency = currency_handle.get_text(strip=True)

            if currency in target_currencies:
                time_cell = row.find('td', class_ = "calendar__time")
                event = row.find('td', class_ = "calendar__event")
                actual = row.find('td', class_ = "calendar__actual")
                forecast = row.find('td', class_ = "calendar__forecast")
                previous = row.find('td', class_ = "calendar__previous")

                actual_text = actual.get_text(strip=True) if actual else ''
                forecast_text = forecast.get_text(strip=True) if forecast else ''
                previous_text = previous.get_text(strip=True) if previous else ''

                if not actual_text and not forecast_text and not previous_text:
                    continue

                impact_cell = row.find('td', class_='calendar__impact')
                if impact_cell:
                    img = impact_cell.find('img')
                    if img:
                        src = img.get('src', '')
                        if 'gra' in src:
                            impact_text = 'Non-Economic'
                        elif 'yel' in src:
                            impact_text = 'Low'
                        elif 'ora' in src:
                            impact_text = 'Medium'
                        elif 'red' in src:
                            impact_text = 'High'
                        else:
                            impact_text = ''
                    else:
                        impact_text = ''
                else:
                    impact_text = ''

                result.append({
                    'date': current_date,
                    'time': time_cell.get_text(strip= True) if time_cell else '',
                    'currency': currency,
                    'event': event.get_text(strip= True) if event else '',
                    'impact': impact_text,
                    'actual': actual_text,
                    'forecast': forecast_text,
                    'previous': previous_text
                })
    return result

def weeks_from_then_tonow(year, month, date):
    start_date = datetime(year, month, date)
    end_date = datetime.today()

    while start_date <= end_date:
        try:
            weekly_data_scraped(start_date.strftime("%b%#d.%Y").lower())
            print(f"Scraping the week: {start_date.strftime('%b%#d.%Y').lower()}")
        except Exception as e:
            print(f"Failed: {start_date.strftime('%b%#d.%Y').lower()} — {e}")


        # after every week, save what you have so far
        pd.DataFrame(result).to_csv("database/raw/economic_calendar_raw.csv", index=False)
        start_date += timedelta(days= 7)
        time.sleep(random.uniform(4, 6))

    return result

if __name__ == '__main__':

    driver = uc.Chrome(version_main = 148)
    data = weeks_from_then_tonow(2026, 3, 8)
    driver.quit()

    for row in data[:5]:
        print(row)

    print(f"Total rows: {len(data)}")