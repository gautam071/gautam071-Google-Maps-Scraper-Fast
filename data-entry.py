import json
import csv
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
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
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)

    # Load Maps once (important for stability)
    driver.get("https://www.google.com/maps")
    time.sleep(5)

    return driver

# ---------------- SEARCH (URL BASED) ---------------- #

def search(driver, keyword, city):
    query = f"{keyword} in {city}"
    print(f"\n🔍 {query}")

    try:
        url = "https://www.google.com/maps/search/" + query.replace(" ", "+")
        driver.get(url)
        time.sleep(5)
        return True
    except Exception:
        print("❌ URL search failed")
        return False

# ---------------- SAFE LISTINGS WAIT ---------------- #

def wait_for_listings(driver, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        try:
            listings = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            if listings:
                return listings
        except:
            pass
        time.sleep(0.5)
    return []

# ---------------- PANEL CHANGE WAIT ---------------- #

def wait_for_place_change(driver, old_url, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        try:
            if driver.current_url != old_url:
                return True
        except:
            pass
        time.sleep(0.3)
    return False

# ---------------- BUSINESS FILTER ---------------- #

def is_relevant_business(name, driver):
    name_l = name.lower()

    # Exclude ONLY obvious retail
    retail_pattern = r"\b(store|showroom|boutique|mall|fashion|clothing|apparel|wear)\b"
    if re.search(retail_pattern, name_l):
        return False

    try:
        category_el = driver.find_elements(
            By.CSS_SELECTOR, "button[jsaction*='pane.rating.category']"
        )
        if category_el:
            cat = category_el[0].text.lower()
            if re.search(retail_pattern, cat):
                return False
    except:
        pass

    return True

# ---------------- FAST SCRAPER (CRASH SAFE) ---------------- #

def scrape_fast(driver, keyword, city, csv_filename, counters):

    listings = wait_for_listings(driver)
    if not listings:
        print("❌ No listings found")
        return

    print(f"➡️ Total listings found: {len(listings)}")

    for i in range(len(listings)):
        try:
            # Always refetch listings (DOM changes constantly)
            listings = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            if i >= len(listings):
                break

            place = listings[i]

            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", place
            )
            time.sleep(0.5)

            old_url = driver.current_url
            driver.execute_script("arguments[0].click();", place)

            # ✅ CRITICAL: wait until panel switches
            if not wait_for_place_change(driver, old_url):
                counters["skipped"] += 1
                print("⚠️ Skipped (panel did not change)")
                continue

            time.sleep(1)

            name_el = driver.find_element(By.CLASS_NAME, "DUwDvf")
            name = name_el.text.strip()

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
            print("⚠️ Skipped (panel error)")
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
