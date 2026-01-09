from selenium.webdriver.common.by import By
from config import Config
from utils.logger import logger
from utils.safe_actions import SafeActions
from selenium.webdriver.support.ui import Select
import time
from utils.helpers import take_screenshot

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
        # 3. Manual CAPTCHA Pause
        print("\n" + "="*60)
        print("⚠️  ATENCIÓN REQUERIDA  ⚠️")
        print("1. Resuelve el CAPTCHA en el navegador.")
        print("2. NO hagas click en Login todavía.")
        print("3. Una vez escrito el CAPTCHA, vuelve aquí.")
        input("👉 PRESIONA ENTER PARA CONTINUAR...")
        print("="*60 + "\n")

        # 3.1 Select Sucursal (Pre-Auth)
        # REMOVED per User Request: Sucursal selection is not needed.
        # if not self.select_sucursal_target(): ...

        # 3.2 Click Login
        logger.info("Clicking Login button...")
        if not self.actions.click((By.CSS_SELECTOR, "#btn_access")):
             logger.error("Failed to click Login button.")
             return False
        
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
    def select_sucursal_target(self):
        """
        Post-login: Auto-selects the required Sucursal.
        Target: "DACTA SAC 2021 , DIVISION TI, OFI. LIMA"
        """
        logger.info("--- Starting Auto-Selection of Sucursal ---")
        
        # Exact target and keywords for fallback
        TARGET_FULL = "DACTA SAC 2021 , DIVISION TI, OFI. LIMA"
        KEYWORDS = ["DIVISION TI", "OFI. LIMA"]
        
        try:
            # Give time for Dashboard/Combos to load after login
            time.sleep(3)
            
            # Strategy 1: Find standard <select> elements
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            logger.info(f"Found {len(selects)} visible <select> elements.")
            
            for element in selects:
                if not element.is_displayed():
                    continue
                    
                try:
                    dropdown = Select(element)
                    
                    # Search options
                    found_option = None
                    for opt in dropdown.options:
                        text = opt.text.strip().upper()
                        # Strict check or Loose check
                        if TARGET_FULL.upper() in text:
                            found_option = opt
                            break
                        
                        # Fallback check
                        if all(k in text for k in KEYWORDS):
                            found_option = opt
                            break
                    
                    if found_option:
                        logger.info(f"Found target Sucursal in dropdown: '{found_option.text}'")
                        
                        # If already selected, skip
                        if found_option.is_selected():
                            logger.info("Target Sucursal is already selected.")
                            return True
                            
                        # Select it
                        dropdown.select_by_visible_text(found_option.text)
                        logger.info("Selected Sucursal. Waiting for page reload...")
                        time.sleep(3) # Wait for potential refresh
                        
                        # Verify
                        if found_option.is_selected():
                             logger.info("CONFIRMED: Sucursal selected successfully.")
                             return True
                        else:
                             # Re-read to check if it stuck
                             pass

                except Exception as ex:
                    logger.debug(f"Skipping a select element: {ex}")
                    
            logger.warning("Could not find target Sucursal in any standard <select>.")
            take_screenshot(self.driver, "fail_select_sucursal")
            return False

        except Exception as e:
            logger.error(f"Error during Sucursal selection: {e}")
            take_screenshot(self.driver, "error_sucursal")
            return False
