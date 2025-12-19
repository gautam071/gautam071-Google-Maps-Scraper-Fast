# Google Maps Scraper (Fast Mode)

## Overview
This project is a **fast Google Maps scraper built with Selenium (Python 3)**.  
It searches Google Maps using keywords and cities defined in a `config.json` file, extracts essential business details, and saves them into a CSV file.

The scraper is optimized for **speed**, avoids unnecessary deep scraping, and focuses only on **mandatory business data** useful for lead generation and analysis.

---

## Features
- Fast Google Maps search using keywords + city
- Reads configuration from `config.json`
- Appends data into a single CSV file
- Extracts only essential fields (no heavy panel scraping)
- Gracefully handles:
  - No results
  - Partial results
  - Missing phone / website
- Designed for **Python 3**
- Headless Chrome supported

---

## Mandatory Fields Collected
The scraper saves the following fields:

| Field | Description |
|-----|------------|
| `name` | Business name |
| `phone` | Phone number (if available) |
| `website` | Website URL (optional) |
| `googlemaps_link` | Google Maps share/page URL |
| `keyword` | Search keyword used |
| `city` | City / location used |

---

## Requirements

Before running the script, ensure you have:

- **Python 3.8+**
- **Google Chrome**
- **ChromeDriver** (matching your Chrome version)
- Python packages:
  ```bash
  pip install selenium

- **Things need to create in code base**
    - config.json
    - places_data.csv
