# Google Maps Scraper (Fast Mode)

## Overview
This project is a **fast Google Maps scraper built with Selenium (Python 3)**.  
It searches Google Maps using **categories (keywords)** and **target locations** from a `config.json` file and extracts only the **most important business data** at high speed.

The scraper is optimized to:
- Avoid slow scrolling logic
- Click results quickly
- Save data reliably to CSV
- Handle “no results” cases safely
- Work without hard-coding brand filters (no Zudio / Allen Solly lists)

This tool is ideal for **B2B lead generation**, **local business research**, and **market mapping**.

---

## Features
- 🚀 Fast Google Maps scraping (no infinite scroll)
- 📁 Uses `config.json` for categories, locations, and output file
- 🧾 Saves data incrementally to CSV (no data loss)
- 📞 Extracts phone numbers when available
- 🌐 Extracts website (optional)
- 🔗 Saves Google Maps share link
- 🏷️ Stores keyword & city used for search
- ⚠️ Handles empty / no-result searches gracefully
- ❌ No hard-coded brand filtering

---

## Mandatory Fields Collected
The scraper guarantees these fields (when available):

- `name` – Business name  
- `phone` – Phone number  
- `website` – Website URL (optional)  
- `googlemaps_link` – Google Maps share link  
- `keyword` – Search keyword/category  
- `city` – Target city/location  

---

## Requirements

Before running the script, ensure you have:

- **Python 3.8+**
- **Google Chrome (latest)**
- **ChromeDriver** (matching your Chrome version)
- Python packages:
  ```bash
  pip install selenium

## Project Structure :
Google-Maps-Scraper-Fast/
│
├── data-entry.py        # Main scraper script
├── config.json          # Configuration file
├── output.csv           # Generated automatically
└── README.md
