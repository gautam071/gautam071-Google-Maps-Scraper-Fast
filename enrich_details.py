import json
import csv
import time
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import InvalidSessionIdException


# ---------------- PHONE NORMALIZATION ---------------- #

def normalize_indian_phone(phone_raw):
    if not phone_raw:
        return ""

    digits = re.sub(r"\D", "", phone_raw)

    if digits.startswith("91") and len(digits) > 10:
        digits = digits[-10:]
    elif digits.startswith("0") and len(digits) > 10:
        digits = digits[-10:]

    return digits if len(digits) == 10 else ""


# ---------------- CONFIG & PROGRESS ---------------- #

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_progress():
    try:
        with open("progress.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"harvested": [], "enriched": []}

def save_progress(section, value):
    data = load_progress()
    if value not in data[section]:
        data[section].append(value)
    with open("progress.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------------- CSV SAVE ---------------- #

def save_row(row, filename):
    headers = ["name", "phone", "website", "googlemaps_link", "keyword", "city"]
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, headers)
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(row)


# ---------------- DRIVER MANAGEMENT ---------------- #

def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(options=options)

def restart_driver(driver):
    try:
        driver.quit()
    except:
        pass

    print("🧊 Cooling down before browser restart...")
    time.sleep(10)   # IMPORTANT cooldown

    return setup_driver()


# ---------------- MAIN ENRICH LOGIC ---------------- #

def main():
    cfg = load_config()
    progress = load_progress()

    driver = setup_driver()

    MAX_PER_SESSION = 15          # SAFE for macOS + Maps
    processed_in_session = 0

    with open(cfg["harvest_file"], newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            link = row["googlemaps_link"]

            if link in progress["enriched"]:
                continue

            # -------- SAFE GET WITH RETRY + SKIP -------- #

            success = False

            for attempt in range(2):   # max 2 attempts
                try:
                    driver.get(link)
                    success = True
                    break
                except (InvalidSessionIdException, Exception):
                    print("⚠️ Browser crashed, restarting driver...")
                    driver = restart_driver(driver)

            if not success:
                print("❌ Skipping link due to repeated crash")
                save_progress("enriched", link)
                continue

            # -------- WAIT FOR PANEL -------- #

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "DUwDvf"))
                )
            except:
                save_progress("enriched", link)
                continue

            # -------- PHONE EXTRACTION -------- #

            phone = ""
            phone_el = driver.find_elements(By.CSS_SELECTOR, '[data-item-id^="phone"]')
            if phone_el:
                raw_phone = phone_el[0].text.strip()
                phone = normalize_indian_phone(raw_phone)

            # Skip if no valid phone
            if not phone:
                save_progress("enriched", link)
                continue

            # -------- WEBSITE -------- #

            website = ""
            web_el = driver.find_elements(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
            if web_el:
                website = web_el[0].get_attribute("href")

            # -------- SAVE -------- #

            save_row({
                "name": row["name"],
                "phone": phone,
                "website": website,
                "googlemaps_link": link,
                "keyword": row["keyword"],
                "city": row["city"]
            }, cfg["enriched_file"])

            save_progress("enriched", link)
            processed_in_session += 1

            print(f"✅ Enriched: {row['name']}")

            # -------- PREVENTIVE RESTART -------- #

            if processed_in_session >= MAX_PER_SESSION:
                print("🔄 Preventive browser restart")
                driver = restart_driver(driver)
                processed_in_session = 0

            time.sleep(cfg["cooldown_between_clicks"])

    driver.quit()
    print("✅ ENRICH PHASE COMPLETE")


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    main()
