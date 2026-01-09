import os
import csv
import json
from datetime import datetime
from config import Config
from utils.logger import logger

def take_screenshot(driver, name="screenshot"):
    if not driver:
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitize name
    name = "".join([c for c in name if c.isalpha() or c.isdigit() or c=='_']).rstrip()
    filename = f"{name}_{timestamp}.png"
    path = os.path.join(Config.EVIDENCE_DIR, filename)
    try:
        driver.save_screenshot(path)
        logger.info(f"Screenshot saved: {path}")
        return path
    except Exception as e:
        logger.error(f"Failed to take screenshot: {e}")
        return None

def save_inventory_json(data, filename="inventory.json"):
    path = os.path.join(Config.OUTPUT_DIR, filename)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Inventory saved to JSON: {path}")
    except Exception as e:
        logger.error(f"Failed to save JSON inventory: {e}")

def save_inventory_csv(data, filename="inventory.csv"):
    path = os.path.join(Config.OUTPUT_DIR, filename)
    if not data:
        return
        
    try:
        keys = ["timestamp", "menu_level_1", "menu_level_2", "menu_level_3", "item_text", "selector_hint", "action_type", "url_after_click", "status", "error"]
        
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for row in data:
                # Filter row to only include keys we care about, or ensure keys presence
                filtered_row = {k: row.get(k, "") for k in keys}
                writer.writerow(filtered_row)
        logger.info(f"Inventory saved to CSV: {path}")
    except Exception as e:
        logger.error(f"Failed to save CSV inventory: {e}")
