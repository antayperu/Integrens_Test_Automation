from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from utils.logger import logger
from utils.waits import Waits

class SafeActions:
    def __init__(self, driver: WebDriver):
        self.driver = driver

    def click(self, locator, timeout=10):
        try:
            element = Waits.wait_for_clickable(self.driver, locator, timeout)
            element.click()
            logger.info(f"Clicked element: {locator}")
            return True
        except Exception as e:
            logger.error(f"Failed to click element {locator}: {e}")
            return False

    def send_keys(self, locator, text, timeout=10):
        try:
            element = Waits.wait_for_visibility(self.driver, locator, timeout)
            element.clear()
            element.send_keys(text)
            logger.info(f"Sent keys to element: {locator}")
            return True
        except Exception as e:
            logger.error(f"Failed to send keys to {locator}: {e}")
            return False
            
    def get_text(self, locator, timeout=10):
        try:
            element = Waits.wait_for_visibility(self.driver, locator, timeout)
            return element.text
        except Exception as e:
            logger.error(f"Failed to get text from {locator}: {e}")
            return None
