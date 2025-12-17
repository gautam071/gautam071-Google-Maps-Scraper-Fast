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
from selenium.common.exceptions import StaleElementReferenceException

# ---------------- CONFIG ---------------- #

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------- CSV SAVE (YOUR STYLE) ---------------- #

def save_to_csv(data_list, csv_filename):
    with open(csv_filename, mode="a", newline="", encoding="utf-8") as f:
        fieldnames = [
            "name",
            "phone",
            "website",
            "googlemaps_link",
            "category",
            "zone"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if f.tell() == 0:
            writer.writeheader()
        writer.writerows(data_list)

# ---------------- DRIVER ---------------- #

def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.google.com/maps")
    return driver

# ---------------- SEARCH ---------------- #

def search(driver, category, location):
    print(f"🔍 {category} | {location}")

    box = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "searchboxinput"))
    )
    box.clear()
    box.send_keys(f"{category} in {location}")
    box.send_keys(Keys.ENTER)

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "hfpxzc"))
    )
    time.sleep(2)

# ---------------- SCRAPE ---------------- #

def scrape_results(driver, category, location, csv_filename, max_results=30):
    collected = set()
    index = 0

    while index < max_results:
        try:
            places = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            if index >= len(places):
                break

            place = places[index]
            driver.execute_script("arguments[0].scrollIntoView(true);", place)
            driver.execute_script("arguments[0].click();", place)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "DUwDvf"))
            )

            name = driver.find_element(By.CLASS_NAME, "DUwDvf").text
            if name in collected:
                index += 1
                continue

            collected.add(name)

            phone = ""
            phone_el = driver.find_elements(By.CSS_SELECTOR, '[data-item-id^="phone"]')
            if phone_el:
                phone = phone_el[0].text

            website = ""
            web_el = driver.find_elements(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
            if web_el:
                website = web_el[0].get_attribute("href")

            data = {
                "name": name,
                "phone": phone,
                "website": website,
                "googlemaps_link": driver.current_url,
                "category": category,
                "zone": location
            }

            save_to_csv([data], csv_filename)
            print(f"✅ Saved: {name}")

            index += 1
            time.sleep(0.8)

        except StaleElementReferenceException:
            continue
        except Exception as e:
            print("⚠️ Skipped one result (panel not loaded)")
            index += 1

# ---------------- MAIN ---------------- #

def main():
    config = load_config()
    driver = setup_driver()

    for category in config["categories"]:
        for location in config["target_locations"]:
            search(driver, category, location)
            scrape_results(
                driver,
                category,
                location,
                config["csv_filename"],
                max_results=30
            )

    driver.quit()
    print("🎯 DONE")

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    main()
