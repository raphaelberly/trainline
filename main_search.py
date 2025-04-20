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
options.add_argument("--disable-plugins")
options.add_argument("--disable-sync")
options.add_argument("--disable-background-networking")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--headless")

try:
    LOGGER.info('Starting Chrome driver')
    service = ChromeService(credentials.get('chromedriver') or ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    searches = yaml.safe_load(open('conf/search.yaml'))

    for search in searches:
        driver.get(search["url"])
        LOGGER.info(f'Loaded page for: {search["key"]}')
        time.sleep(5)
        for train in search["trains"]:
            # for cookie_button in driver.find_elements(by='xpath', value='//*[text()="Continuer sans accepter"]'):
            #     cookie_button.click()
            # LOGGER.debug(f'Refused cookies')
            # time.sleep(2)
            driver.execute_script("window.scrollTo(0, 380)")
            trip = driver.find_element(by='xpath', value=f'//*[@aria-labelledby="urn:trainline:flex:nonflexi"]/div[{train["target_result"]}]')
            assert train['time'] in trip.text, 'Could not find target train'
            time.sleep(2)

            if trip.get_attribute('data-test-unsellable') == 'true':
                LOGGER.info('Train is unsellable. No notification was sent.')
            elif 'un billet de 2nde classe' not in trip.accessible_name and train['only_second_class']:
                LOGGER.info('Only first class ticket was found. No notification was sent.')
            else:
                push.send_message(f"{train['key']} available", title='🚄 Trainline Alert')
                LOGGER.info('Train is sellable: Notification sent.')

except Exception as e:
    push.send_message("An error occurred", title='⚠️Broken trainline alerting')
    raise e
