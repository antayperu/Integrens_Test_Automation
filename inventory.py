import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import logger
from utils.safe_actions import SafeActions
from utils.waits import Waits
from utils.helpers import save_inventory_json, save_inventory_csv
from config import Config

class InventoryCrawler:
    def __init__(self, driver):
        self.driver = driver
        self.actions = SafeActions(driver)
        self.visited_ids = set() # To track visited items (by unique path ID)
        self.inventory_data = []
        self.menu_root_selector = None

    def run(self):
        logger.info("Starting Inventory Crawl (Dynamic Mode)...")
        
        # 1. Detect Menu
        menu_element = self._detect_menu_root()
        if not menu_element:
            logger.error("Could not detect menu root. Please configure manually or restart.")
            return []
        
        # 2. Start Recursive Crawl
        self._crawl_level(parent_chain=[])
        
        # 3. Save Results
        save_inventory_json(self.inventory_data, "inventory.json")
        save_inventory_csv(self.inventory_data, "inventory.csv")
        
        # Summary
        total = len(self.inventory_data)
        ok = sum(1 for i in self.inventory_data if i['status'] == 'OK')
        fail = total - ok
        logger.info(f"Inventory finished. Total: {total}, OK: {ok}, FAIL: {fail}")
        logger.info(f"Outputs saved in: {Config.OUTPUT_DIR}")
        
        return self.inventory_data

    def _detect_menu_root(self):
        """
        Attempts to find the main menu container and sets the selector.
        """
        candidates = [
            (By.ID, "menu"),
            (By.CLASS_NAME, "menu"), 
            (By.CSS_SELECTOR, "nav"),
            (By.ID, "main-menu"),
            (By.ID, "sidebar-menu"),
            (By.CSS_SELECTOR, ".sidebar"),
            (By.CSS_SELECTOR, "ul.nav")
        ]
        
        for by, val in candidates:
            try:
                elements = self.driver.find_elements(by, val)
                for el in elements:
                    if el.is_displayed():
                        logger.info(f"Menu candidate found: {val}")
                        self.menu_root_selector = (by, val)
                        return el
            except:
                pass
        
        logger.warning("No standard menu found. Attempting fallback to find any list of links...")
        return None

    def _recover_state(self, parent_chain):
        """
        Re-navigates to the specific submenu depth by re-clicking parents.
        Crucial for dynamic apps that reset state on back navigation.
        """
        if not parent_chain:
            # Just ensure menu root is visible
            return self._detect_menu_root() is not None
            
        logger.info(f"Recovering state: {' -> '.join(parent_chain)}")
        
        # Ensure we wait for page to stabilize
        time.sleep(2)
        
        for parent_text in parent_chain:
            # Try to find and click the parent
            try:
                # XPath to find link with exact or partial text
                xpath = f"//a[contains(text(), '{parent_text}')] | //span[contains(text(), '{parent_text}')]"
                
                element = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((By.XPATH, xpath))
                )
                
                # Check if visible and click to expand
                if element.is_displayed():
                    element.click()
                    time.sleep(1) # Wait for animation/load
                
            except Exception as e:
                logger.warning(f"Error recovering parent '{parent_text}': {e}")
                return False
                
        return True

    def _crawl_level(self, parent_chain):
        """
        Robust Crawling:
        1. Scan: Identify all candidates (Text) at this level.
        2. Loop: Process each candidate by re-finding it.
        """
        level = len(parent_chain) + 1
        logger.info(f"Scanning Level {level} | Context: {parent_chain}")
        
        # --- PHASE 1: SCAN ---
        item_identifiers = []
        try:
            # Wait for menu root visibility
            if self.menu_root_selector:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(self.menu_root_selector)
                )
                menu_root = self.driver.find_element(*self.menu_root_selector)
                
                # Find all logical items (links)
                links = menu_root.find_elements(By.TAG_NAME, "a")
                
                # Filter visible and meaningful
                for link in links:
                    if link.is_displayed():
                        text = link.text.strip()
                        if text:
                            # Verify if we have visited this exact path
                            unique_id = " -> ".join(parent_chain + [text])
                            if unique_id not in self.visited_ids:
                                item_identifiers.append({
                                    "text": text,
                                    "unique_id": unique_id
                                })
            else:
                 logger.error("Menu root selector missing during scan.")
                 return

        except Exception as e:
            logger.error(f"Scan failed at level {level}: {e}")
            return

        logger.info(f"Found {len(item_identifiers)} items to process at this level.")

        # --- PHASE 2: PROCESS ---
        for item_def in item_identifiers:
            text = item_def['text']
            unique_id = item_def['unique_id']
            
            # Skip if visited (concurrency safety)
            if unique_id in self.visited_ids:
                continue
            
            self.visited_ids.add(unique_id)
            
            logger.info(f"Processing Item: {text}")
            
            entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "menu_level_1": parent_chain[0] if len(parent_chain) > 0 else text,
                "menu_level_2": parent_chain[1] if len(parent_chain) > 1 else (text if len(parent_chain)==1 else ""),
                "menu_level_3": parent_chain[2] if len(parent_chain) > 2 else (text if len(parent_chain)==2 else ""),
                "item_text": text,
                "selector_hint": f"//a[contains(text(), '{text}')]",
                "action_type": "click",
                "status": "PENDING"
            }
            
            navigated = False
            
            try:
                # 1. Re-Find Element (Stale-proof strategy)
                xpath = f"//a[contains(text(), '{text}')]" 
                
                element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                
                # Check attributes before click (heuristic for submenu vs link)
                href = element.get_attribute("href")
                is_submenu = (href is None) or (href == "") or ("#" in href) or ("javascript" in href)
                
                # 2. Click
                element.click()
                
                # 3. Wait for reaction
                time.sleep(3) 
                
                # 4. Check Result
                current_url = self.driver.current_url
                
                if current_url != Config.URL_LOGIN and "wf_login" not in current_url:
                     entry['status'] = "OK"
                     entry['url_after_click'] = current_url
                     
                     if is_submenu:
                         # It looks like a submenu, check if new items appeared
                         # Recurse
                         self._crawl_level(parent_chain + [text])
                     else:
                         # Likely navigated to a module
                         navigated = True

                else:
                    entry['status'] = "FAIL"
                    entry['error'] = "Logged out or invalid URL"

            except Exception as e:
                logger.error(f"Error clicking {text}: {e}")
                entry['status'] = "FAIL"
                entry['error'] = str(e)
            
            self.inventory_data.append(entry)
            
            # --- PHASE 3: RECOVER ---
            if navigated:
                logger.info("Navigated away. Returning to menu...")
                self.driver.back()
                time.sleep(2) # Wait for page load
                
                # Recover state (re-open parents)
                if not self._recover_state(parent_chain):
                    logger.error(f"Failed to recover state after {text}. Stopping this branch.")
                    return 
