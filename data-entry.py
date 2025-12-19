import json
import csv
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

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
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.google.com/maps")
    return driver

# ---------------- SEARCH ---------------- #

def search(driver, keyword, city):
    print(f"\n🔍 {keyword} | {city}")

    try:
        search_box = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "searchboxinput"))
        )
        search_box.clear()
        search_box.send_keys(f"{keyword} in {city}")
        search_box.send_keys(Keys.ENTER)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "hfpxzc"))
        )
        time.sleep(2)

    except TimeoutException:
        print("❌ Search failed. Skipping.")
        return False

    return True

# ---------------- BUSINESS FILTER (FIXED) ---------------- #

def is_relevant_business(name, driver):
    """
    KEEP all textile-related units
    REMOVE only obvious retail / fashion stores
    """

    name_l = name.lower()

    # ❌ Strong retail-only exclusion
    retail_pattern = r"\b(store|showroom|boutique|mall|fashion|clothing|apparel|wear)\b"
    if re.search(retail_pattern, name_l):
        return False

    # ❌ Google Maps category check (retail)
    try:
        category_el = driver.find_elements(By.CSS_SELECTOR, "button[jsaction*='pane.rating.category']")
        if category_el:
            cat = category_el[0].text.lower()
            if re.search(retail_pattern, cat):
                return False
    except:
        pass

    # ✅ Everything else is allowed (textile-friendly)
    return True

# ---------------- FAST SCRAPER ---------------- #

def scrape_fast(driver, keyword, city, csv_filename, counters):
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "hfpxzc"))
        )
    except TimeoutException:
        print("❌ No listings found")
        return

    listings = driver.find_elements(By.CLASS_NAME, "hfpxzc")
    print(f"➡️ Total listings found: {len(listings)}")

    for place in listings:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", place)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", place)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "DUwDvf"))
            )

            name = driver.find_element(By.CLASS_NAME, "DUwDvf").text.strip()

            if not is_relevant_business(name, driver):
                counters["excluded"] += 1
                print(f"⏭️ Excluded retail: {name}")
                continue

            phone = ""
            phone_el = driver.find_elements(By.CSS_SELECTOR, '[data-item-id^="phone"]')
            if phone_el:
                phone = phone_el[0].text.strip()

            website = ""
            web_el = driver.find_elements(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
            if web_el:
                website = web_el[0].get_attribute("href")

            data = {
                "name": name,
                "phone": phone,
                "website": website,
                "googlemaps_link": driver.current_url,
                "keyword": keyword,
                "city": city
            }

            save_to_csv(data, csv_filename)
            counters["saved"] += 1
            print(f"✅ Saved: {name}")

            time.sleep(1)

        except (TimeoutException, StaleElementReferenceException):
            counters["skipped"] += 1
            print("⚠️ Skipped (panel issue)")
            continue

# ---------------- MAIN ---------------- #

def main():
    config = load_config()
    categories = config["categories"]
    locations = config["target_locations"]
    csv_filename = config["csv_filename"]

    counters = {
        "saved": 0,
        "excluded": 0,
        "skipped": 0
    }

    driver = setup_driver()

    for category in categories:
        for location in locations:
            if search(driver, category, location):
                scrape_fast(driver, category, location, csv_filename, counters)

    driver.quit()

    print("\n🎯 SCRAPING COMPLETED")
    print(f"✅ Saved (textile units): {counters['saved']}")
    print(f"⏭️ Excluded retail: {counters['excluded']}")
    print(f"⚠️ Skipped (errors): {counters['skipped']}")

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    main()
