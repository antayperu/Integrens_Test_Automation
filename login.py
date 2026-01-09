from selenium.webdriver.common.by import By
from config import Config
from utils.logger import logger
from utils.safe_actions import SafeActions
from utils.waits import Waits

class LoginFlow:
    def __init__(self, driver):
        self.driver = driver
        self.actions = SafeActions(driver)

    def login(self):
        """
        Executes the login flow with manual CAPTCHA resolution.
        """
        logger.info("Navigate to login page...")
        self.driver.get(Config.URL_LOGIN)
        
        # 1. Fill credentials
        logger.info("Filling credentials...")
        if not self.actions.send_keys((By.CSS_SELECTOR, "#txt_codusu"), Config.USER):
            logger.error("Failed to enter username.")
            return False
            
        if not self.actions.send_keys((By.CSS_SELECTOR, "#txt_passwd"), Config.PASS):
            logger.error("Failed to enter password.")
            return False

        # 2. Focus on CAPTCHA input for user convenience (optional)
        try:
            self.driver.find_element(By.CSS_SELECTOR, "#txt_capcha").click()
        except:
            pass

        # 3. Manual CAPTCHA Pause
        print("\n" + "="*60)
        print("⚠️  ATENCIÓN REQUERIDA  ⚠️")
        print(f"Por favor, resuelve el CAPTCHA en el navegador y haz click en LOGIN ({'#btn_access'}).")
        print("Una vez que hayas ingresado exitosamente al sistema...")
        input("👉 PRESIONA ENTER PARA CONTINUAR...")
        print("="*60 + "\n")

        # 4. Validate Login
        return self._validate_login_success()

    def _validate_login_success(self):
        """
        Verifies if login was successful by checking URL change and login form disappearance.
        """
        logger.info("Validating login status...")
        
        # Check if URL changed
        current_url = self.driver.current_url
        if current_url == Config.URL_LOGIN:
            logger.warning("URL did not change. Still on login page?")
            # Check if login button is still visible
            try:
                Waits.wait_for_visibility(self.driver, (By.CSS_SELECTOR, "#btn_access"), timeout=3)
                logger.error("Login failed: URL unchanged and Default Login Button still visible.")
                
                retry = input("Login failed. Retry validation? (y/n): ")
                if retry.lower() == 'y':
                    return self._validate_login_success()
                return False
            except:
                logger.info("Login button not visible, assuming success despite URL match (maybe redirect pending or SPA).")
                return True
        
        logger.info(f"Login successful. Current URL: {current_url}")
        return True
