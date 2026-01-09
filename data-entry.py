import json
import csv
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ---------------- GLOBAL DEDUPE ---------------- #

SEEN_BUSINESSES = set()
SEEN_LINKS = set()

# ---------------- CONFIG ---------------- #

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------- CSV SAVE ---------------- #

def save_to_csv(data, filename):
    fieldnames = [
        "name",
        "phone",
        "website",
        "googlemaps_link",
        "keyword",
        "city"
    ]
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(data)

# ---------------- DRIVER ---------------- #

def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    driver.get("https://www.google.com/maps")
    return driver

# ---------------- SEARCH (URL BASED) ---------------- #

def search(driver, keyword, city):
    query = f"{keyword} in {city}".replace(" ", "+")
    url = f"https://www.google.com/maps/search/{query}"
    print(f"\n🔍 {keyword} | {city}")

    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(4)
        return True
    except:
        print("❌ Page load failed")
        return False

# ---------------- SCROLL RESULTS PANEL ---------------- #

def scroll_results_panel(driver, max_scrolls=20, pause=1.5):
    """
    Scroll feed if available.
    If feed does not exist, return visible listings safely.
    """

    listings = driver.find_elements(By.CLASS_NAME, "hfpxzc")

    try:
        panel = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
    except:
        return listings  # non-feed layout

    last_count = len(listings)

    for _ in range(max_scrolls):
        driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight",
            panel
        )
        time.sleep(pause)

        listings = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        if len(listings) == last_count:
            break
        last_count = len(listings)

    return listings

# ---------------- FILTERS ---------------- #

def is_temporarily_closed(place):
    try:
        return "temporarily closed" in place.text.lower()
    except:
        return False

def is_relevant_business(name):
    retail_pattern = r"\b(store|showroom|boutique|mall|fashion|clothing|apparel|wear)\b"
    return not re.search(retail_pattern, name.lower())

# ---------------- WAIT FOR PANEL CHANGE ---------------- #

def wait_for_place_change(driver, old_url, timeout=8):
    end = time.time() + timeout
    while time.time() < end:
        if driver.current_url != old_url:
            return True
        time.sleep(0.3)
    return False

# ---------------- SCRAPER ---------------- #

def scrape_fast(driver, keyword, city, csv_filename, counters):

    listings = scroll_results_panel(driver)
    if not listings:
        print("⚠️ No listings visible for this keyword")
        return

    print(f"➡️ Listings loaded: {len(listings)}")

    for place in listings:
        try:
            name = place.get_attribute("aria-label")
            link = place.get_attribute("href")

            if not name or not link:
                continue

            name_key = name.lower().strip()

            # 1️⃣ Skip duplicates
            if name_key in SEEN_BUSINESSES or link in SEEN_LINKS:
                continue

            # 2️⃣ Skip temporarily closed
            if is_temporarily_closed(place):
                continue

            # 3️⃣ Skip retail
            if not is_relevant_business(name):
                counters["excluded"] += 1
                continue

            # Click only when needed
            old_url = driver.current_url
            driver.execute_script("arguments[0].click();", place)

            if not wait_for_place_change(driver, old_url):
                counters["skipped"] += 1
                continue

            time.sleep(1)

            phone = ""
            phone_el = driver.find_elements(By.CSS_SELECTOR, '[data-item-id^="phone"]')
            if phone_el:
                phone = phone_el[0].text.strip()

            # 4️⃣ Skip if no phone
            if not phone:
                counters["skipped"] += 1
                continue

            website = ""
            web_el = driver.find_elements(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
            if web_el:
                website = web_el[0].get_attribute("href")

            data = {
                "name": name.strip(),
                "phone": phone,
                "website": website,
                "googlemaps_link": driver.current_url,
                "keyword": keyword,
                "city": city
            }

            save_to_csv(data, csv_filename)

            SEEN_BUSINESSES.add(name_key)
            SEEN_LINKS.add(link)

            counters["saved"] += 1
            print(f"✅ Saved: {name}")

            time.sleep(0.8)

        except:
            counters["skipped"] += 1
            continue

# ---------------- MAIN ---------------- #

def main():
    config = load_config()
    categories = config["categories"]
    locations = config["target_locations"]
    csv_filename = config["csv_filename"]

    counters = {"saved": 0, "excluded": 0, "skipped": 0}

    driver = setup_driver()

    for category in categories:
        for location in locations:
            if search(driver, category, location):
                scrape_fast(driver, category, location, csv_filename, counters)

    driver.quit()

    print("\n🎯 SCRAPING COMPLETED")
    print(f"✅ Saved: {counters['saved']}")
    print(f"⏭️ Excluded retail: {counters['excluded']}")
    print(f"⚠️ Skipped: {counters['skipped']}")

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    main()
