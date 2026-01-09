import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import logger
from utils.safe_actions import SafeActions
from utils.waits import Waits
from utils.helpers import save_inventory_json, save_inventory_csv, take_screenshot
from config import Config

class InventoryCrawler:
    def __init__(self, driver):
        self.driver = driver
        self.actions = SafeActions(driver)
        self.visited_ids = set() 
        self.inventory_data = []
        # Main menu selector
        self.menu_root_selector = (By.CSS_SELECTOR, "nav, #menu, .sidebar, ul.nav, #main-menu") 

    def run(self):
        logger.info("Starting Inventory Crawl (Robust Dynamic Mode)...")
        if not self._ensure_menu_visible():
             logger.error("Menu root not found at start. Aborting.")
             return []
        
        self._crawl_level(parent_chain=[])
        
        save_inventory_json(self.inventory_data, "inventory.json")
        save_inventory_csv(self.inventory_data, "inventory.csv")
        return self.inventory_data

    def _ensure_menu_visible(self):
        """
        Ensures we are in default content and menu is visible.
        """
        self.driver.switch_to.default_content()
        try:
             # Basic check to see if we can find any menu-like structure
             # Using a broad union selector for improved detection
             Waits.wait_for_visibility(self.driver, self.menu_root_selector, timeout=5)
             return True
        except:
             logger.warning("Main menu not immediately visible.")
             return False

    def _crawl_level(self, parent_chain):
        level = len(parent_chain) + 1
        logger.info(f"Scanning Level {level} | Context: {parent_chain}")
        
        # 1. SCAN PHASE: Get Text Identifiers
        item_identifiers = []
        try:
            self._ensure_menu_visible()
            # Find all visible links in the menu area
            # We assume menu is on default content
            potential_links = self.driver.find_elements(By.CSS_SELECTOR, "nav a, #menu a, .sidebar a, ul.nav a")
            
            for link in potential_links:
                 try:
                     if link.is_displayed():
                         text = link.text.strip()
                         if text:
                             # Check Uniqueness (Path + Text)
                             unique_id = " -> ".join(parent_chain + [text])
                             if unique_id not in self.visited_ids:
                                 item_identifiers.append(text)
                 except:
                     pass # Stale element during scan, ignore
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            return

        logger.info(f"Items to process: {item_identifiers}")

        # 2. PROCESS PHASE
        for text in item_identifiers:
            unique_id = " -> ".join(parent_chain + [text])
            if unique_id in self.visited_ids:
                continue
            
            self.visited_ids.add(unique_id)
            
            entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "menu_level_1": parent_chain[0] if len(parent_chain) > 0 else text,
                "menu_level_2": parent_chain[1] if len(parent_chain) > 1 else (text if len(parent_chain)==1 else ""),
                "menu_text": text,
                "status": "PENDING"
            }
            
            try:
                # 2.1 Re-Find Element (Fresh)
                logger.info(f"Processing: {text}")
                self._ensure_menu_visible()
                
                # Robust partial text match
                xpath = f"//a[contains(text(), '{text}')]"
                element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                
                # 2.2 Robust Click
                if self.actions.robust_click(element):
                    time.sleep(3) # Wait for UI reaction
                    
                    # 2.3 Check Result
                    # A) Did URL change significantly?
                    # B) Did an iframe appear?
                    # C) Did submenu expand?
                    
                    if self._check_iframe_loaded():
                        entry['status'] = "OK"
                        entry['type'] = "Module (Iframe)"
                        # Go back to menu context
                        self.driver.switch_to.default_content()
                        # If module took full screen or navigated, we might need to restore state??
                        # Usually ERPs with iframes keep the menu on the side (default content).
                        # So we might just need to click next item.
                        # But if it navigated, we need recovery.
                        
                    elif self._did_navigate_away():
                        entry['status'] = "OK"
                        entry['type'] = "Link (Navigate)"
                        self.driver.back()
                        self._recover_state(parent_chain)
                        
                    else:
                        # Maybe submenu expanded?
                        # Check if new items are visible that match 'level+1' criteria?
                        # For recursion simplicity, we just recurse if we suspect it's a folder.
                        # How to know? 
                        # We blindly recurse. If scan finds nothing new, it returns quickly.
                        # Optimization: Check if 'expanded' class exists on parent <li>?
                        entry['status'] = "OK"
                        entry['type'] = "Submenu/Action"
                        self._crawl_level(parent_chain + [text])

                else:
                     entry['status'] = "FAIL"
                     entry['error'] = "Click failed"
                     take_screenshot(self.driver, f"fail_click_{text}")

            except Exception as e:
                logger.error(f"Error processing {text}: {e}")
                entry['status'] = "FAIL"
                entry['error'] = str(e)
                take_screenshot(self.driver, f"error_{text}")
                # Try recovery
                self._recover_state(parent_chain)

            self.inventory_data.append(entry)

    def _check_iframe_loaded(self):
        """
        Checks if a content iframe allows switching.
        """
        try:
            # Common iframe names/ids
            iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe")
            self.driver.switch_to.frame(iframe)
            # If successful, we assume content loaded.
            # Optional: Check for body/div
            logger.info("  -> Iframe detected and switched.")
            return True
        except:
            return False
            
    def _did_navigate_away(self):
        return Config.URL_LOGIN not in self.driver.current_url and "wf_login" not in self.driver.current_url

    def _recover_state(self, parent_chain):
        """
        Restores menu state by clicking parents in order.
        """
        if not parent_chain:
            return
        
        logger.info(f"Recovering state: {parent_chain}")
        self._ensure_menu_visible()
        time.sleep(1)
        
        for p_text in parent_chain:
            try:
                xpath = f"//a[contains(text(), '{p_text}')]"
                el = self.driver.find_element(By.XPATH, xpath)
                if el.is_displayed():
                    self.actions.robust_click(el)
                    time.sleep(1)
            except:
                logger.warning(f"Could not re-click parent: {p_text}")
