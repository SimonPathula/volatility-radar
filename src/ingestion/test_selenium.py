import time 
from selenium import webdriver
from selenium.webdriver.common.by import By

url = "https://www.forexfactory.com/calendar?week=jan3.2022" 
driver = webdriver.Chrome()
driver.get(url)

time.sleep(3)  # wait for page to fully load

page_source = driver.page_source

start = page_source.find('calendar__table')
print(page_source[start:start+3000])

driver.close()

