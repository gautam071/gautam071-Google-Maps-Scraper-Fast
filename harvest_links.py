import json, csv, time, re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------------- GLOBAL DEDUPE ---------------- #

SEEN_LINKS = set()
SEEN_NAMES = set()

# ---------------- CONFIG & PROGRESS ---------------- #

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_progress():
    try:
        with open("progress.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"harvested": []}

def save_progress(value):
    data = load_progress()
    if value not in data["harvested"]:
        data["harvested"].append(value)
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
    print("🧊 Cooling down before browser restart...")
    time.sleep(10)
    return setup_driver()

# ---------------- SCROLL ---------------- #

def scroll_results(driver, max_scrolls=15):
    try:
        panel = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
    except:
        return driver.find_elements(By.CLASS_NAME, "hfpxzc")

    last_count = 0
    for _ in range(max_scrolls):
        driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight", panel
        )
        time.sleep(1.5)
        items = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        if len(items) == last_count:
            break
        last_count = len(items)
    return items

# ---------------- CSV SAVE ---------------- #

def save_row(row, filename):
    headers = ["name", "googlemaps_link", "keyword", "city"]
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, headers)
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(row)

# ---------------- CATEGORY-BASED FILTER ---------------- #

RETAIL_PATTERN = re.compile(
    r"\b(store|showroom|boutique|mall|fashion|clothing|apparel|wear)\b",
    re.IGNORECASE
)

def is_temporarily_closed(place):
    try:
        return "temporarily closed" in place.text.lower()
    except:
        return False


def is_relevant_business(place):
    """
    PRIMARY: Google Maps category (button.DkEaL[jsaction*='.category'])
    FALLBACK: business name
    """

    # 1️⃣ CATEGORY CHECK (PRIMARY & MOST ACCURATE)
    try:
        category_buttons = place.find_elements(
            By.CSS_SELECTOR,
            "button.DkEaL[jsaction*='.category']"
        )

        if category_buttons:
            category_text = category_buttons[0].text.lower()

            # Exclude retail-only categories
            if RETAIL_PATTERN.search(category_text):
                return False

            # Non-retail category → accept immediately
            return True
    except:
        pass

    # 2️⃣ NAME CHECK (FALLBACK ONLY)
    try:
        name = place.get_attribute("aria-label") or ""
        if RETAIL_PATTERN.search(name.lower()):
            return False
    except:
        pass

    # Default: allow
    return True

# ---------------- MAIN ---------------- #

def main():
    cfg = load_config()
    progress = load_progress()
    driver = setup_driver()

    processed_in_session = 0
    MAX_PER_SESSION = 25   # safe limit

    for keyword in cfg["categories"]:
        for city in cfg["target_locations"]:
            query_key = f"{keyword}|{city}"

            if query_key in progress["harvested"]:
                continue

            print(f"\n🔍 Harvesting: {keyword} | {city}")
            url = f"https://www.google.com/maps/search/{keyword}+in+{city}"
            driver.get(url)

            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(4)

            listings = scroll_results(driver)
            print(f"➡️ Listings found: {len(listings)}")

            for place in listings:
                name = place.get_attribute("aria-label")
                link = place.get_attribute("href")

                # ❌ Skip temporarily closed businesses
                if is_temporarily_closed(place):
                    continue

                # ❌ Skip retail / fashion businesses
                if not is_relevant_business(name):
                    continue

                if not name or not link:
                    continue

                name_key = name.lower().strip()

                # 🚫 GLOBAL DUPLICATE BLOCK
                if link in SEEN_LINKS or name_key in SEEN_NAMES:
                    continue

                save_row({
                    "name": name.strip(),
                    "googlemaps_link": link,
                    "keyword": keyword,
                    "city": city
                }, cfg["harvest_file"])

                SEEN_LINKS.add(link)
                SEEN_NAMES.add(name_key)

            save_progress(query_key)
            processed_in_session += 1

            # 🔄 Preventive browser restart
            if processed_in_session >= MAX_PER_SESSION:
                print("🔄 Preventive browser restart")
                driver = restart_driver(driver)
                processed_in_session = 0

            time.sleep(cfg["cooldown_between_searches"])

    driver.quit()
    print("✅ HARVEST COMPLETE")

if __name__ == "__main__":
    main()
