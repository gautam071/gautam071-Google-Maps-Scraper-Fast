Google Maps Scraper
====================================

Overview
--------

This project is a **robust, resume-safe Google Maps scraping pipeline** designed specifically to collect **textile-related businesses** such as:

*   Textile mills
    
*   Weaving units
    
*   Handloom units
    
*   Towel / bedsheet manufacturers
    
*   Yarn and fabric producers
    

The system avoids aggressive scraping, minimizes Google blocking, and is suitable for **CRM imports, market research, and lead generation**.

Why This Architecture?
----------------------

Google Maps is highly dynamic and fragile when scraped directly via UI clicks.To solve this, the project uses a **two-phase pipeline**:

1.  **Harvest Phase** – safely collects business names and Google Maps links
    
2.  **Enrichment Phase** – opens collected links to extract phone numbers and websites
    

This separation makes the scraper:

*   More stable
    
*   Easier to resume
    
*   Much less likely to crash or get blocked
    

Features
--------

*   URL-based Google Maps search (no fragile search box automation)
    
*   Scrolls beyond the first page (50–100+ results per keyword)
    
*   Filters out:
    
    *   Clothing stores & fashion retail
        
    *   Malls & showrooms
        
    *   Temporarily closed businesses
        
*   Skips listings without phone numbers
    
*   Normalizes Indian phone numbers to **10-digit format**
    
*   Deduplicates businesses automatically
    
*   Resume support using progress.json
    
*   Logging to file for debugging & audits
    
*   Auto-backoff delays to reduce Google throttling
    

Project Structure
-----------------
Google-Maps-Scraper/  
│  
├── config.json                # Keywords, cities, delays, file paths  
├── progress.json              # Resume state (auto-generated)  
├── run_pipeline.py            # Runs harvest + enrich sequentially  
│  
├── harvest_links.py           # Phase 1: Collect names & Maps links  
├── enrich_details.py          # Phase 2: Collect phone & website  
├── logger_setup.py            # Logging configuration  
│  
├── data/     
  ├── harvested_links.csv  
  │   
  └── enriched_results.csv  
│  
└── logs/      
  ├── harvest_YYYYMMDD.log      
  └── enrich_YYYYMMDD.log   `

Requirements
------------

*   Python **3.9+**
    
*   Google Chrome (latest recommended)
    
*   ChromeDriver (must match Chrome version)
    

### Install Dependencies

Plain 
`   pip install selenium   `

Configuration (config.json)
---------------------------

All searches and behavior are controlled from config.json.

### Example
`   {    "categories": ["as","dsf"],    "target_locations": ["abs"],    "harvest_file": "data/harvested_links.csv",    "enriched_file": "data/enriched_results.csv",    "cooldown_between_searches": 5,    "cooldown_between_clicks": 2  }   `

How the Pipeline Works
----------------------

### Phase 1 – Harvest (harvest\_links.py)

*   Uses Google Maps search URLs
    
*   Scrolls the results panel
    
*   Collects:
    
    *   Business name
        
    *   Google Maps link
        
    *   Keyword
        
    *   City
        
*   No place panel clicks
    
*   Extremely stable and fast
    

Run:
`   python harvest_links.py   `

### Phase 2 – Enrich (enrich\_details.py)

*   Opens each saved Google Maps link
    
*   Extracts:
    
    *   Phone number (India normalized)
        
    *   Website (if available)
        
*   Skips businesses without phone numbers
    
*   Deduplicates automatically
    

Run:
`   python enrich_details.py   `

Run Everything Automatically (Recommended)
------------------------------------------

Use the pipeline runner:
`   python run_pipeline.py   `

This:

1.  Runs the harvest phase
    
2.  Then runs the enrich phase
    
3.  Resumes safely if interrupted
    

Resume & Crash Recovery
-----------------------

### Stop the script

Press:
`   Ctrl + C   `

### Resume later

Re-run the same command:
`   python run_pipeline.py   `

Already processed keywords and businesses are skipped automatically using progress.json.

Phone Number Normalization (India)
----------------------------------

All phone numbers are normalized to:
` XXXXXXXXXX   `

Handled formats include:

*   +91 98765 43210
    
*   091-94433-01111
    
*   044 2466 1234
    

Invalid or incomplete numbers are ignored.

Logging
-------

Logs are written to the logs/ directory.

Each run generates timestamped logs for:

*   Harvest phase
    
*   Enrichment phase
    

Logs include:

*   Progress tracking
    
*   Errors & retries
    
*   Skipped reasons
    
*   Timing information
    

Auto-Backoff (Google Safety)
----------------------------

To avoid Google blocking:

*   Adds delays between searches
    
*   Adds delays between clicks
    
*   Slows down automatically when pages load slowly
    

This allows **long-running, stable scrapes**.

Output Files
------------

### data/harvested\_links.csv

Fields:

*   name
    
*   googlemaps\_link
    
*   keyword
    
*   city
    

### data/enriched\_results.csv

Fields:

*   name
    
*   phone
    
*   website
    
*   googlemaps\_link
    
*   keyword
    
*   city
    

Both files are **CRM-ready**.

Recommended Use Cases
---------------------

*   Textile industry lead generation
    
*   Supplier discovery
    
*   Market research
    
*   CRM population
    
*   Territory analysis
    

Important Notes
---------------

*   This project avoids aggressive scraping by design
    
*   Google Maps limits results; scrolling and delays are required
    
*   Clicking every listing directly will cause crashes — this pipeline prevents that

Re-running, Resuming & Resetting the Pipeline
---------------------------------------------

This project is designed to be **resume-safe**. You can stop the script at any time and continue later **without data loss or duplication**.

### How Progress Is Tracked

*   Progress is stored in progress.json
    
*   It has two sections:
    
    *   "harvested" → completed keyword + city searches
        
    *   "enriched" → Google Maps links already enriched
        
*   CSV files are **append-only** (never overwritten)
    

### Re-run Enrichment Using Existing Harvested Data

If harvesting has already completed and you only want to enrich:
`   python enrich_details.py   `

*   Uses existing harvested\_links.csv
    
*   Skips already enriched links
    
*   Continues safely from where it stopped
    

### Re-run Both Harvest and Enrich (Normal Use)

To run the full pipeline again:
`   python run_pipeline.py   `

*   Skips already completed harvests
    
*   Skips already enriched businesses
    
*   Automatically resumes
    

### Stop the Script Safely

At any time, press:
`   Ctrl + C   `

You can restart later using the same command.

### Force a Full Re-run (Start Fresh)

If you want to **re-enrich everything again**:
`   rm progress.json   `

Then run:
`   python run_pipeline.py   `

⚠️ Do **not** delete CSV files unless you intentionally want to discard data.

### What NOT to Delete

*   ❌ Do NOT delete harvested\_links.csv unless restarting from scratch
    
*   ❌ Do NOT edit CSV files while scripts are running