import time
import yaml
from selenium import webdriver

from lib.push import Push

push_credentials = yaml.safe_load(open('conf/secrets.yaml'))['push']
push = Push(**push_credentials)

options = webdriver.ChromeOptions()
options.add_argument("--disable-extensions")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1000x800")
options.add_argument("--headless")

driver = webdriver.Chrome(options=options)

trains_to_check = yaml.safe_load(open('conf/search.yaml'))

for train in trains_to_check:
    driver.get(train["url"])
    print(f'Loaded page for: {train["key"]}')
    time.sleep(2)
    for cookie_button in driver.find_elements(by='xpath', value='//*[text()="Continuer sans accepter"]'):
        cookie_button.click()
    print(f'Refused cookies')
    time.sleep(2)

    trip = driver.find_element(by='xpath', value=f'//*[@aria-labelledby="urn:trainline:flex:nonflexi"]/div[{train["target_result"]-1}]')
    time.sleep(2)

    if trip.get_attribute('data-test-unsellable') == 'true':
        print('Train is unsellable')
    else:
        push.send_message("A train is available", title='🚄 Trainline Alert')
        print('Train is sellable: Notification sent.')
