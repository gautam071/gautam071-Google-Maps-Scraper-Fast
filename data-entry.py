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

    search_box = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "searchboxinput"))
    )

    search_box.clear()
    search_box.send_keys(f"{keyword} in {city}")
    search_box.send_keys(Keys.ENTER)

    time.sleep(4)  # allow results to load

# ---------------- RELEVENT BUSINESS ---------------- #

def is_relevant_business(name, keyword, driver):
    """
    Returns True if business looks like a manufacturer / textile unit,
    False if it looks like a clothing retail store
    """

    name_l = name.lower()
    keyword_l = keyword.lower()

    # --- 1️⃣ Must loosely match search intent ---
    if not any(k in name_l for k in keyword_l.split()):
        return False

    # --- 2️⃣ Exclude retail-only patterns (logic based) ---
    retail_patterns = [
        r"\b(store|showroom|boutique|mall|fashion|clothing|apparel|wear)\b"
    ]

    for pattern in retail_patterns:
        if re.search(pattern, name_l):
            return False

    # --- 3️⃣ Check Google Maps category (if visible) ---
    category_elements = driver.find_elements(By.CSS_SELECTOR, "button[jsaction*='pane.rating.category']")
    if category_elements:
        category_text = category_elements[0].text.lower()
        if any(x in category_text for x in ["clothing", "apparel", "fashion", "store"]):
            return False

    return True

# ---------------- FAST SCRAPER ---------------- #

def scrape_fast(driver, keyword, city, csv_filename):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "hfpxzc"))
        )
    except:
        print("❌ No results found")
        return

    listings = driver.find_elements(By.CLASS_NAME, "hfpxzc")
    print(f"➡️ Found {len(listings)} results")

    for index in range(len(listings)):
        try:
            listings = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            driver.execute_script("arguments[0].click();", listings[index])

            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CLASS_NAME, "DUwDvf"))
            )

            name = driver.find_element(By.CLASS_NAME, "DUwDvf").text.strip()

            phone = ""
            phone_el = driver.find_elements(By.CSS_SELECTOR, '[data-item-id^="phone"]')
            if phone_el:
                phone = phone_el[0].text.strip()

            website = ""
            web_el = driver.find_elements(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
            if web_el:
                website = web_el[0].get_attribute("href")

            if not is_relevant_business(name, keyword, driver):
                print(f"⏭️ Skipped (irrelevant): {name}")
                continue

            data = {
                "name": name,
                "phone": phone,
                "website": website,
                "googlemaps_link": driver.current_url,
                "keyword": keyword,
                "city": city
            }

            save_to_csv(data, csv_filename)
            print(f"✅ Saved: {name}")

            time.sleep(1)

        except Exception as e:
            print("⚠️ Skipped one result (panel not loaded)")
            continue

# ---------------- MAIN ---------------- #

def main():
    config = load_config()
    categories = config["categories"]
    locations = config["target_locations"]
    csv_filename = config["csv_filename"]

    driver = setup_driver()

    for category in categories:
        for location in locations:
            search(driver, category, location)
            scrape_fast(driver, category, location, csv_filename)

    driver.quit()
    print("\n🎯 SCRAPING COMPLETED")

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    main()
