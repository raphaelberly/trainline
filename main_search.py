import logging
import time
import yaml
from selenium import webdriver

from lib.logger import configure_logging
from lib.push import Push
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
configure_logging(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


credentials = yaml.safe_load(open('conf/secrets.yaml'))
push = Push(**credentials['push'])

options = webdriver.ChromeOptions()
options.add_argument("--disable-extensions")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1000x800")
options.add_argument("--headless")

try:
    service = ChromeService(credentials.get('chromedriver') or ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    trains_to_check = yaml.safe_load(open('conf/search.yaml'))

    for train in trains_to_check:
        driver.get(train["url"])
        LOGGER.info(f'Loaded page for: {train["key"]}')
        time.sleep(2)
        for cookie_button in driver.find_elements(by='xpath', value='//*[text()="Continuer sans accepter"]'):
            cookie_button.click()
        LOGGER.info(f'Refused cookies')
        time.sleep(2)

        trip = driver.find_element(by='xpath', value=f'//*[@aria-labelledby="urn:trainline:flex:nonflexi"]/div[{train["target_result"]}]')
        assert trip.text.startswith(train['time']), 'Could not find target train'
        time.sleep(2)

        if trip.get_attribute('data-test-unsellable') == 'true':
            LOGGER.info('Train is unsellable. No notification was sent.')
        else:
            push.send_message("A train is available", title='🚄 Trainline Alert')
            LOGGER.info('Train is sellable: Notification sent.')

except Exception as e:
    push.send_message("An error occurred", title='⚠️Broken trainline alerting')
    raise e
