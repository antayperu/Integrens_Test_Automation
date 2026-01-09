import time
from selenium.webdriver.common.by import By
from utils.logger import logger
from utils.helpers import save_inventory_json, save_inventory_csv, take_screenshot
from config import Config

class InventoryCrawler:
    def __init__(self, driver):
        self.driver = driver
        self.inventory_data = []
        # Scope: Sidebar
        self.side_menu_selector = (By.CSS_SELECTOR, "aside, .sidebar, #sidebar-menu, #main-menu, .main-sidebar, .page-sidebar") 

    def run(self):
        logger.info("Starting Inventory Capture (Assisted Mode)...")
        
        # 1. Ensure Sidebar is there
        sidebar = self._get_sidebar_element()
        if not sidebar:
             logger.error("Sidebar container not verified. Cannot proceed.")
             return []

        # 2. User Prompt
        print("\n" + "="*60)
        print("🖐️  INVENTARIO ASISTIDO  🖐️")
        print("1. Ve al navegador.")
        print("2. EXPANDE MANUALMENTE todos los menús que desees incluir (ej. Comercial, Logística).")
        print("3. Asegúrate de que los submenús sean visibles.")
        print("4. Cuando estés listo, vuelve aquí.")
        input("👉 PRESIONA ENTER PARA CAPTURAR...")
        print("="*60 + "\n")

        # 3. Capture Evidence
        take_screenshot(self.driver, "sidebar_expanded")
        logger.info("Screenshot captured: outputs/evidence/sidebar_expanded.png")

        # 4. Parse DOM
        self._parse_sidebar_structure(sidebar)

        # 5. Save Results
        save_inventory_json(self.inventory_data, "inventory.json")
        save_inventory_csv(self.inventory_data, "inventory.csv")
        
        # Summary
        l1_count = len(set([i['menu_level_1'] for i in self.inventory_data if i['menu_level_1']]))
        l2_count = len([i for i in self.inventory_data if i['menu_level_2']])
        
        logger.info(f"Inventory Captured. Modules (L1): {l1_count}, Submenus (L2): {l2_count}")
        logger.info(f"Outputs saved in: {Config.OUTPUT_DIR}")
        
        return self.inventory_data

    def _get_sidebar_element(self):
        try:
            self.driver.switch_to.default_content()
            elements = self.driver.find_elements(*self.side_menu_selector)
            for el in elements:
                if el.is_displayed():
                    return el
            return None
        except:
            return None

    def _parse_sidebar_structure(self, sidebar_element):
        """
        Parses the visible DOM hierarchy to infer L1/L2 items.
        Assumes standard list structure (ul/li).
        """
        try:
            # Find all List Items (li) that are potentially menu items
            # Common structure: sidebar > ul > li (Level 1) > ul > li (Level 2)
            
            # Strategy: Find all visible links (a) and determine their depth based on parents.
            links = sidebar_element.find_elements(By.TAG_NAME, "a")
            
            logger.info(f"Scanning {len(links)} potential links in sidebar...")
            
            current_l1 = ""
            
            for link in links:
                if not link.is_displayed():
                    continue
                    
                text = link.text.strip()
                if not text or text in ["Toggle navigation", "Ayuda", "Sign out", "Salir"]:
                    continue

                # Determine Level by checking parents
                # Heuristic: 
                # If parent is 'nav' or top 'ul' -> Level 1
                # If parent is 'li' inside nested 'ul' -> Level 2
                
                # We can check specific class names if known, or just use indentation logic?
                # Using XPath to count 'ul' ancestors is reliable.
                try:
                    # Count how many UL ancestors exist for this element
                    # Note: Selenium doesn't give simple ancestor count easily without iterate.
                    # We can assume: 
                    # If it has a 'fa-angle-down' or similar icon, it MIGHT be a parent.
                    # If the click expands something...
                    
                    # Simpler Heuristic for Integrens:
                    # Does it have a submenu sibling? 
                    # (This is hard to detect passively reliably without specific DOM knowledge)
                    
                    # Let's assume sequential reading:
                    # PROBABLY: L1 items are followed by their L2 children.
                    # But we need to know WHICH is which.
                    
                    # Let's try to detect nesting via DOM.
                    # Check if 'ul' parent has class 'sidebar-menu' (Root) or 'treeview-menu' (Nested)?
                    parent_ul = link.find_element(By.XPATH, "./ancestor::ul[1]")
                    parent_classes = parent_ul.get_attribute("class")
                    
                    level = 1
                    if "treeview-menu" in parent_classes or "dropdown-menu" in parent_classes or "submenu" in parent_classes:
                        level = 2
                    # Fallback: if it's inside a 'li' that is inside another 'ul' that is NOT the root?
                    
                    entry = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "menu_level_1": "",
                        "menu_level_2": "",
                        "item_text": text,
                        "status": "CAPTURED",
                        "notes": f"Detected at Level {level}"
                    }
                    
                    if level == 1:
                        current_l1 = text
                        entry["menu_level_1"] = text
                    else:
                        entry["menu_level_1"] = current_l1
                        entry["menu_level_2"] = text
                        
                    self.inventory_data.append(entry)

                except Exception as ex:
                    logger.debug(f"Parsing item error: {ex}")
                    # Fallback add
                    self.inventory_data.append({
                        "item_text": text,
                        "status": "CAPTURED_RAW",
                        "error": str(ex)
                    })

        except Exception as e:
            logger.error(f"Error parsing sidebar DOM: {e}")
