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
        # STRICT Scope: Sidebar / Aside
        self.side_menu_selector = (By.CSS_SELECTOR, "aside, .sidebar, #sidebar-menu, #main-menu, .main-sidebar") 

    def run(self):
        logger.info("Starting Inventory Crawl (Sidebar Scoped)...")
        if not self._ensure_menu_visible():
             logger.error("Sidebar not found. Aborting.")
             return []
        
        # Start at Level 1
        self._crawl_level(parent_chain=[])
        
        save_inventory_json(self.inventory_data, "inventory.json")
        save_inventory_csv(self.inventory_data, "inventory.csv")
        return self.inventory_data

    def _ensure_menu_visible(self):
        """
        Escapes iframes and verifies sidebar visibility.
        """
        try:
            self.driver.switch_to.default_content()
            Waits.wait_for_visibility(self.driver, self.side_menu_selector, timeout=5)
            return True
        except:
             logger.warning("Sidebar not found or not visible.")
             return False

    def _get_sidebar_element(self):
        try:
            return self.driver.find_element(*self.side_menu_selector)
        except:
            return None

    def _crawl_level(self, parent_chain):
        level = len(parent_chain) + 1
        logger.info(f"Scanning Level {level} | Context: {parent_chain}")
        
        # 1. SCAN PHASE: Get Text Identifiers (Scoped to Sidebar)
        item_identifiers = []
        try:
            self._ensure_menu_visible()
            sidebar = self._get_sidebar_element()
            
            if sidebar:
                # Find links ONLY within the sidebar
                # We try to be smart: if Level 1, find direct children? 
                # For generic robustness, we find ALL visible links and filter by what hasn't been visited?
                # Or better: We find visible links. If hierarchy is strict `ul > li > a`, we could use that.
                # Let's use visible links for now but filter aggressively.
                
                # Exclude common non-menu items explicitly if needed
                potential_links = sidebar.find_elements(By.TAG_NAME, "a")
                
                for link in potential_links:
                     try:
                         if link.is_displayed():
                             text = link.text.strip()
                             # Exclude empty or obviously wrong texts
                             if text and text not in ["", "Toggle navigation", "Ayuda"]: 
                                 unique_id = " -> ".join(parent_chain + [text])
                                 
                                 # Heuristic: If we are deep (level > 1), ensure this link "belongs" to current parent?
                                 # Hard to know without strict DOM hierarchy. 
                                 # For robust crawling, we assume if it's visible in sidebar and new, it's valid.
                                 
                                 if unique_id not in self.visited_ids:
                                     # Avoid re-clicking parents?
                                     if text not in parent_chain: 
                                        item_identifiers.append(text)
                     except:
                         pass
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            return

        logger.info(f"Items to process at Level {level}: {item_identifiers}")

        # 2. PROCESS PHASE
        for text in item_identifiers:
            unique_id = " -> ".join(parent_chain + [text])
            if unique_id in self.visited_ids:
                continue
            
            self.visited_ids.add(unique_id)
            safe_text_filename = "".join([c if c.isalnum() else "_" for c in text])
            
            entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "menu_level_1": parent_chain[0] if len(parent_chain) > 0 else text,
                "menu_level_2": parent_chain[1] if len(parent_chain) > 1 else (text if len(parent_chain)==1 else ""),
                "item_text": text,
                "status": "PENDING",
                "selector_hint": f"Sidebar -> {text}",
                "error_type": "",
                "error": ""
            }
            
            try:
                # 2.1 Re-Find Element (Fresh & Scoped)
                logger.info(f"Processing: {text}")
                self._ensure_menu_visible()
                sidebar = self._get_sidebar_element()
                
                # Scoped XPath within sidebar
                # "descendant::a" ensures we look inside sidebar
                xpath = f".//a[contains(text(), '{text}')]"
                
                element = WebDriverWait(sidebar, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                
                # Pre-Click Screenshot
                take_screenshot(self.driver, f"L{level}_before_{safe_text_filename}")

                # 2.2 Robust Click
                if self.actions.robust_click(element):
                    time.sleep(3) # Wait for animation/load
                    
                    # Post-Click Screenshot
                    take_screenshot(self.driver, f"L{level}_after_{safe_text_filename}")

                    # 2.3 Analyze Result
                    if self._check_iframe_loaded():
                        entry['status'] = "OK"
                        entry['action_type'] = "Module Load (Iframe)"
                        entry['url_after_click'] = self.driver.current_url
                        # Recovery: Switch back to default content to continue menu
                        self.driver.switch_to.default_content()
                        
                    elif self._did_navigate_away():
                        entry['status'] = "OK"
                        entry['action_type'] = "Page Navigation"
                        entry['url_after_click'] = self.driver.current_url
                        # Recovery: Back + State Restore
                        self.driver.back()
                        self._recover_state(parent_chain)
                        
                    else:
                        # Accordion Expansion?
                        # If we are here, likely the menu just expanded.
                        entry['status'] = "OK"
                        entry['action_type'] = "Menu Expansion"
                        entry['url_after_click'] = self.driver.current_url
                        
                        # Recurse: Look for new items (children)
                        # We pass the new chain.
                        self._crawl_level(parent_chain + [text])

                else:
                     entry['status'] = "FAIL"
                     entry['error_type'] = "ClickFailure"
                     entry['error'] = "Robust click returned False"
                     take_screenshot(self.driver, f"fail_click_{safe_text_filename}")

            except Exception as e:
                err_type = type(e).__name__
                err_msg = str(e)
                logger.error(f"Error processing {text}: {err_type} - {err_msg}")
                entry['status'] = "FAIL"
                entry['error_type'] = err_type
                entry['error'] = err_msg
                take_screenshot(self.driver, f"error_{safe_text_filename}")
                self._recover_state(parent_chain)

            self.inventory_data.append(entry)

    def _check_iframe_loaded(self):
        try:
            iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe")
            if iframe.is_displayed():
                self.driver.switch_to.frame(iframe)
                # Check for some content?
                logger.info("  -> Iframe detected.")
                return True
            return False
        except:
            return False
            
    def _did_navigate_away(self):
        try:
            # Check if sidebar is GONE
            self.driver.find_element(*self.side_menu_selector)
            return False
            # Or check URL whitelist?
        except:
            return True

    def _recover_state(self, parent_chain):
        if not parent_chain:
            return
        
        logger.info(f"Recovering state: {parent_chain}")
        self._ensure_menu_visible()
        time.sleep(1)
        
        for p_text in parent_chain:
            try:
                # Find parent in sidebar
                sidebar = self._get_sidebar_element()
                xpath = f".//a[contains(text(), '{p_text}')]"
                el = sidebar.find_element(By.XPATH, xpath)
                if el.is_displayed():
                    self.actions.robust_click(el)
                    time.sleep(1)
            except:
                logger.warning(f"Could not re-click parent: {p_text}")
