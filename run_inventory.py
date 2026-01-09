from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from config import Config
from login import LoginFlow
from inventory import InventoryCrawler
from utils.logger import logger

def main():
    logger.info("Initializing Integrens Test Automation...")
    
    # Setup Driver
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        driver.maximize_window()
        driver.implicitly_wait(Config.Config.WAIT_TIMEOUT if hasattr(Config, 'WAIT_TIMEOUT') else 5)
    except  Exception as e:
         # Fallback for manual path or newer selenium versions
        logger.warning(f"Webdriver manager failed, trying default: {e}")
        driver = webdriver.Chrome()
        driver.maximize_window()

    try:
        # 1. Login
        login_flow = LoginFlow(driver)
        if not login_flow.login():
            logger.error("Login failed or aborted. Exiting.")
            return
        # 2. Inventory
        crawler = InventoryCrawler(driver)
        crawler.run()
        
    except Exception as e:
        logger.critical(f"Critical execution error: {e}")
    finally:
        logger.info("Closing driver...")
        driver.quit()
        print("\n\nExecution Finished. Check outputs/ directory for results.")

if __name__ == "__main__":
    main()
