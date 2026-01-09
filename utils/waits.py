from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
# from utils.logger import logger # Import if needed, avoiding circular imports if logger imports waits

class Waits:
    DEFAULT_TIMEOUT = 10

    @staticmethod
    def wait_for_element(driver, locator, timeout=DEFAULT_TIMEOUT, condition=EC.presence_of_element_located):
        try:
            return WebDriverWait(driver, timeout).until(condition(locator))
        except TimeoutException:
            raise

    @staticmethod
    def wait_for_clickable(driver, locator, timeout=DEFAULT_TIMEOUT):
        return Waits.wait_for_element(driver, locator, timeout, EC.element_to_be_clickable)
    
    @staticmethod
    def wait_for_visibility(driver, locator, timeout=DEFAULT_TIMEOUT):
        return Waits.wait_for_element(driver, locator, timeout, EC.visibility_of_element_located)
