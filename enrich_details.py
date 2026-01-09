import json, csv, time, re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import InvalidSessionIdException

# ---------------- GLOBAL DEDUPE ---------------- #

SEEN_LINKS = set()
SEEN_NAMES = set()

# ---------------- PHONE NORMALIZER ---------------- #

def normalize_indian_phone(phone_raw):
    if not phone_raw:
        return ""
    digits = re.sub(r"\D", "", phone_raw)
    if digits.startswith("91"):
        digits = digits[-10:]
    if digits.startswith("0"):
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
        return {"enriched": []}

def save_progress(value):
    data = load_progress()
    if value not in data["enriched"]:
        data["enriched"].append(value)
    with open("progress.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ---------------- DRIVER ---------------- #

def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def restart_driver(driver):
    try:
        driver.quit()
    except:
        pass
    time.sleep(8)
    return setup_driver()

# ---------------- CSV SAVE ---------------- #

def save_row(row, filename):
    headers = ["name", "phone", "website", "googlemaps_link", "keyword", "city"]
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, headers)
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(row)

# ---------------- MAIN ---------------- #

def main():
    cfg = load_config()
    progress = load_progress()
    driver = setup_driver()

    with open(cfg["harvest_file"], newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            link = row["googlemaps_link"]
            name_key = row["name"].lower().strip()

            # 🚫 GLOBAL DUPLICATE BLOCK
            if link in progress["enriched"]:
                continue
            if link in SEEN_LINKS or name_key in SEEN_NAMES:
                continue

            success = False
            for _ in range(2):
                try:
                    driver.get(link)
                    success = True
                    break
                except InvalidSessionIdException:
                    driver = restart_driver(driver)

            if not success:
                save_progress(link)
                continue

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "DUwDvf"))
                )
            except:
                save_progress(link)
                continue

            phone = ""
            p = driver.find_elements(By.CSS_SELECTOR, '[data-item-id^="phone"]')
            if p:
                phone = normalize_indian_phone(p[0].text.strip())

            if not phone:
                save_progress(link)
                continue

            website = ""
            w = driver.find_elements(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
            if w:
                website = w[0].get_attribute("href")

            save_row({
                "name": row["name"],
                "phone": phone,
                "website": website,
                "googlemaps_link": link,
                "keyword": row["keyword"],
                "city": row["city"]
            }, cfg["enriched_file"])

            SEEN_LINKS.add(link)
            SEEN_NAMES.add(name_key)
            save_progress(link)

            print(f"✅ Enriched: {row['name']}")
            time.sleep(cfg["cooldown_between_clicks"])

    driver.quit()
    print("✅ ENRICH COMPLETE")

if __name__ == "__main__":
    main()
