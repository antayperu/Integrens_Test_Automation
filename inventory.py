import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException
from utils.logger import logger
from utils.safe_actions import SafeActions
from utils.waits import Waits
from utils.helpers import save_inventory_json, save_inventory_csv
from config import Config

class InventoryCrawler:
    def __init__(self, driver):
        self.driver = driver
        self.actions = SafeActions(driver)
        self.visited_ids = set() # To track visited items (by text path)
        self.inventory_data = []
        self.menu_root_selector = None

    def run(self):
        logger.info("Starting Inventory Crawl...")
        
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
        Re-navigates to the specific submenu depth.
        parent_chain: List of texts of parent items to click.
        """
        if not parent_chain:
            return True
            
        logger.info(f"Recovering state: {' -> '.join(parent_chain)}")
        
        # Ensure we are at menu root (refresh might be needed if full page reload happened)
        # Assuming we can just click through from current page top
        
        current_context_selector = self.menu_root_selector
        
        for parent_text in parent_chain:
            # Find parent item in current context
            found = False
            try:
                # Find all potential items
                # Depending on implementation, we look for links containing text
                # We use a broad generic locator
                items = self.driver.find_elements(By.XPATH, f"//a[contains(text(), '{parent_text}')] | //span[contains(text(), '{parent_text}')]")
                
                for item in items:
                    if item.is_displayed() and parent_text in item.text:
                        item.click()
                        time.sleep(1) # Small wait for expand animation
                        found = True
                        break
            except Exception as e:
                logger.warning(f"Error recovering state for {parent_text}: {e}")
            
            if not found:
                logger.error(f"Could not recover state for parent: {parent_text}")
                return False
                
        return True

    def _crawl_level(self, parent_chain):
        """
        Crawls items at current level.
        """
        level = len(parent_chain) + 1
        logger.info(f"Crawling Level {level} | Parents: {parent_chain}")
        
        # 1. Identify items in the current 'active' menu view
        # This is tough without selectors. We assume expanded items show children.
        # We need to find items that match the current context.
        # Simplification: We look for all visible links in the menu container 
        # that are NOT in our visited list.
        
        try:
            # Re-find menu root to avoid stale element
            menu_root = self.driver.find_element(*self.menu_root_selector)
            
            # Find all visible links (a) or clickables (span with onclick?)
            # Constrain to visible
            items = menu_root.find_elements(By.TAG_NAME, "a")
        except StaleElementReferenceException:
            logger.warning("Stale menu root. Retrying detection...")
            self._detect_menu_root()
            menu_root = self.driver.find_element(*self.menu_root_selector)
            items = menu_root.find_elements(By.TAG_NAME, "a")
            
        # Filter items: visible and non-empty text
        visible_items = []
        for i in items:
            try:
                if i.is_displayed() and i.text.strip():
                    visible_items.append(i)
            except:
                pass

        # Check which unique items we haven't processed
        # We process by Index logic to avoid stale references during iteration,
        # but indices shift if menus expand.
        # Strategy: Extract needed info (text, selector hint) then process one by one, 
        # re-acquiring the element.
        
        item_definitions = []
        for index, item in enumerate(visible_items):
            try:
                text = item.text.strip()
                # Unique ID for this crawl: Path + Text
                unique_id = " -> ".join(parent_chain + [text])
                
                if unique_id not in self.visited_ids:
                    item_definitions.append({
                        "text": text,
                        "unique_id": unique_id,
                        # We try to get a CSS selector or XPath relative
                        "xpath_hint": self._get_xpath_hint(item)
                    })
            except:
                pass

        logger.info(f"Found {len(item_definitions)} new items at this state.")

        for item_def in item_definitions:
            text = item_def['text']
            unique_id = item_def['unique_id']
            xpath = item_def['xpath_hint']
            
            self.visited_ids.add(unique_id)
            
            # Record preliminary data
            entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "menu_level_1": parent_chain[0] if len(parent_chain) > 0 else text,
                "menu_level_2": parent_chain[1] if len(parent_chain) > 1 else (text if len(parent_chain)==1 else ""),
                "menu_level_3": parent_chain[2] if len(parent_chain) > 2 else (text if len(parent_chain)==2 else ""),
                "item_text": text,
                "selector_hint": xpath,
                "action_type": "click",
                "status": "PENDING"
            }
            
            # --- ACTION PHASE ---
            # 1. Ensure state (re-navigate if we are not sure)
            # Optimization: If we just processed an item that navigated away, we MUST recover.
            # If the previous item was just a submenu expand, we might be OK, but safer to check.
            
            # We will always attempt to find the element again.
            try:
                current_element = self.driver.find_element(By.XPATH, xpath)
                
                # Check if it is a submenu or link
                # Heuristic: href is empty or '#', or has arrow icon
                is_submenu = False
                href = current_element.get_attribute("href")
                if not href or href.endswith("#") or "javascript" in href:
                    is_submenu = True
                
                # Click
                logger.info(f"Clicking: {text}")
                current_element.click()
                time.sleep(2) # Wait for reaction
                
                # Check result
                new_url = self.driver.current_url
                entry['url_after_click'] = new_url
                
                if new_url != Config.URL_LOGIN and "wf_login" not in new_url: # Basic check
                    entry['status'] = "OK"
                else:
                    entry['status'] = "FAIL"
                    entry['error'] = "Logged out or invalid state"

                self.inventory_data.append(entry)

                if is_submenu:
                    # Recurse
                    # Assume menu expanded.
                     self._crawl_level(parent_chain + [text])
                else:
                    # It was a link, likely navigated or changed usage frame.
                    # We need to Go Back or Reset State for the next item.
                    # If URL changed significantly, go back
                    if new_url != Config.URL_LOGIN:
                        self.driver.back()
                        time.sleep(1)
                        # Re-open parents
                        self._recover_state(parent_chain)

            except Exception as e:
                logger.error(f"Error processing {text}: {e}")
                entry['status'] = "FAIL"
                entry['error'] = str(e)
                self.inventory_data.append(entry)
                # Try to recover state just in case
                self._recover_state(parent_chain)

    def _get_xpath_hint(self, element):
        """Helper to generate a unique-ish xpath"""
        try:
            text = element.text.strip()
            return f"//a[contains(text(), '{text}')]"
        except:
            return "//a"
