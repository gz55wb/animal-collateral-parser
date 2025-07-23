# """
# Professional Animal Names and Collateral Adjectives Scraper
# ==========================================================

# A production-level Python application that scrapes Wikipedia's list of animal names,
# extracts collateral adjectives, downloads animal images, and generates HTML reports.

# Author: Raz Zorno
# Date: July 2025
# """

# main.py

import asyncio
from src.core.scraper import AnimalScraper
from src.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    try:
        logger.info("Starting Animal Scraper...")
        scraper = AnimalScraper()
        
        # Run the async scraping process
        animal_entries, report_path, exec_time = asyncio.run(
            scraper.scrape_and_generate_report()
        )
        
        logger.info(f"✅ Done! Report generated: {report_path}")
        print(f"\n🦁 Found {len(animal_entries)} animals.")
        print(f"📄 Report path: {report_path}")
        print(f"⏱ Execution time: {exec_time:.2f} seconds\n")
    
    except Exception as e:
        logger.exception("❌ Scraper failed with error")
        print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    main()
