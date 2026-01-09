from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from utils.logger import logger
from utils.waits import Waits

class SafeActions:
    def __init__(self, driver: WebDriver):
        self.driver = driver

    def click(self, locator, timeout=10):
        """
        Simple click wrapper.
        """
        try:
            element = Waits.wait_for_clickable(self.driver, locator, timeout)
            element.click()
            logger.info(f"Clicked element: {locator}")
            return True
        except Exception as e:
            logger.error(f"Failed to click element {locator}: {e}")
            return False

    def robust_click(self, element):
        """
        Tries 3 strategies to click an element:
        1. Scroll into view + Click
        2. ActionChains Move + Click
        3. JavaScript Click
        """
        try:
            # Strategy 1: Scroll + Standard Click
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                ActionChains(self.driver).move_to_element(element).perform() # Hover to ensure visibility
                element.click()
                logger.info("Robust Click: Standard click successful.")
                return True
            except Exception as e1:
                logger.warning(f"Standard click failed: {e1}. Trying ActionChains...")

            # Strategy 2: ActionChains
            try:
                actions = ActionChains(self.driver)
                actions.move_to_element(element).click().perform()
                logger.info("Robust Click: ActionChains click successful.")
                return True
            except Exception as e2:
                logger.warning(f"ActionChains click failed: {e2}. Trying JS...")

            # Strategy 3: JavaScript Force Click
            self.driver.execute_script("arguments[0].click();", element)
            logger.info("Robust Click: JS click successful.")
            return True

        except Exception as final_e:
            logger.error(f"All click strategies failed: {final_e}")
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
