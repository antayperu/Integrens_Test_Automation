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
        Parses the visible DOM hierarchy to infer L1/L2/L3 items based on nesting depth.
        Uses ancestor counting to determine indentation levels.
        """
        try:
            links = sidebar_element.find_elements(By.TAG_NAME, "a")
            logger.info(f"Scanning {len(links)} potential links in sidebar...")
            
            items_raw = []
            
            # 1. Collect Valid Items and Measure Depth
            for link in links:
                if not link.is_displayed():
                    continue
                    
                text = link.text.strip()
                # Exclude common noise
                if not text or text in ["Toggle navigation", "Ayuda", "Sign out", "Salir", "Usuario", "admin"]:
                    continue

                # Calculate Depth: Number of 'ul' ancestors
                # This is a robust proxy for menu nesting in bootstrap/standard navs
                depth = len(link.find_elements(By.XPATH, "./ancestor::ul"))
                items_raw.append({
                    "text": text,
                    "depth": depth
                })

            if not items_raw:
                logger.warning("No visible items found in sidebar execution.")
                return

            # 2. Normalize Depth (Find minimum depth to be Level 1)
            min_depth = min(item['depth'] for item in items_raw)
            logger.info(f"Depth analysis: Min Depth = {min_depth} (Level 1)")

            # 3. Build Hierarchy
            current_l1 = ""
            current_l2 = ""
            
            for item in items_raw:
                text = item['text']
                raw_depth = item['depth']
                
                # Calculate relative level (1-based)
                level = raw_depth - min_depth + 1
                
                entry = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "menu_level_1": "",
                    "menu_level_2": "",
                    "menu_level_3": "",
                    "item_text": text,
                    "status": "CAPTURED",
                    "notes": f"Depth {raw_depth} -> Level {level}"
                }
                
                if level == 1:
                    current_l1 = text
                    current_l2 = "" # Reset L2 when new L1 starts
                    entry["menu_level_1"] = text
                    
                elif level == 2:
                    current_l1 = current_l1 if current_l1 else "Unknown"
                    current_l2 = text
                    entry["menu_level_1"] = current_l1
                    entry["menu_level_2"] = text
                    
                elif level >= 3:
                     entry["menu_level_1"] = current_l1
                     entry["menu_level_2"] = current_l2
                     entry["menu_level_3"] = text
                
                self.inventory_data.append(entry)

        except Exception as e:
            logger.error(f"Error parsing sidebar structure: {e}")
