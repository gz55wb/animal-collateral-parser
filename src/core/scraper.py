import aiohttp
import time
import requests
import asyncio
from typing import List, Optional, Tuple
from src.core.models import AnimalEntry, ScrapingConfig
from src.core.parser import AnimalDataParser
from pathlib import Path

from src.services.image_downloader import ImageDownloader
from src.services.image_finder import WikipediaImageFinder
from src.services.report_generator import HTMLReportGenerator

from src.utils.decorators import timing_decorator, retry_decorator

from src.utils.logger import get_logger

logger = get_logger(__name__)

class AnimalScraper:
    """Main scraper class that orchestrates the entire operation."""
    
    def __init__(self, config: Optional[ScrapingConfig] = None):
        self.config = config or ScrapingConfig()
        self.parser = AnimalDataParser()
        self.image_finder = WikipediaImageFinder()
        self.image_downloader = ImageDownloader(self.config)
        self.report_generator = HTMLReportGenerator(self.config)
        
        # Ensure the image directory exists
        self.config.image_dir.mkdir(parents=True, exist_ok=True)
    
    @timing_decorator
    async def scrape_and_generate_report(self) -> Tuple[List[AnimalEntry], Path, float]:
        """
        Main method to scrape data and generate report.
        
        Returns:
            Tuple of (animal_entries, report_path, execution_time)
        """
        start_time = time.time()
        
        try:
            # Step 1: Fetch and parse Wikipedia page
            logger.info("Fetching Wikipedia page...")
            html_content = self._fetch_wikipedia_page()
            
            # Step 2: Extract animal-adjective pairs
            logger.info("Parsing animal data...")
            animal_adjective_pairs = self.parser.parse_wikipedia_page(html_content)
            
            if not animal_adjective_pairs:
                raise ValueError("No animal-adjective pairs found on the page")
            
            # Step 3: Create AnimalEntry objects and find images
            logger.info("Creating animal entries and finding images...")
            animal_entries = await self._create_animal_entries(animal_adjective_pairs)
            
            # Step 4: Download images
            logger.info("Downloading images...")
            animal_entries = await self._download_images(animal_entries)
            
            # Step 5: Generate HTML report
            execution_time = time.time() - start_time
            logger.info("Generating HTML report...")
            report_path = self.report_generator.generate_report(animal_entries, execution_time)
            
            logger.info(f"Scraping completed successfully in {execution_time:.2f} seconds")
            logger.info(f"Found {len(animal_entries)} animal entries")
            logger.info(f"Report saved to: {report_path}")
            
            return animal_entries, report_path, execution_time
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Scraping failed after {execution_time:.2f} seconds: {str(e)}")
            raise
    
    @retry_decorator(max_retries=3, delay=2.0)
    def _fetch_wikipedia_page(self) -> str:
        """Fetch the Wikipedia page content."""
        response = requests.get(
            str(self.config.base_url),
            timeout=self.config.request_timeout,
            headers={'User-Agent': 'AnimalScraper/1.0 (Educational Purpose)'}
        )
        response.raise_for_status()
        return response.text
    
    @timing_decorator
    async def _create_animal_entries(self, data_list: List[Tuple[str, str, List[str]]]) -> List[AnimalEntry]:
        timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
        connector = aiohttp.TCPConnector(limit_per_host=self.config.max_concurrent_downloads)

        semaphore = asyncio.Semaphore(self.config.max_concurrent_downloads)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers={'User-Agent': 'AnimalScraper/1.0'}) as session:

            async def create_entry(animal_name, adjective, links):
                async with semaphore:
                    try:
                        image_url = None

                        if links:
                            image_url = await self.image_finder.find_image_from_url_async(links[0], session)

                        if not image_url:
                            image_url = self.image_finder.find_animal_image(animal_name)

                        return AnimalEntry(
                            animal_name=animal_name,
                            collateral_adjective=adjective if adjective.strip() else "N/A",
                            image_url=image_url if image_url else "N/A"
                        )
                    except Exception as e:
                        logger.warning(f"Error creating entry for {animal_name}: {str(e)}")
                        return None

            tasks = [create_entry(animal_name, adjective, links) for animal_name, adjective, links in data_list]

            entries = await asyncio.gather(*tasks)

            return [e for e in entries if e is not None]

    @timing_decorator
    async def _download_images(self, animal_entries: List[AnimalEntry]) -> List[AnimalEntry]:
        """Download images for all animal entries."""
        # Filter entries that have image URLs
        entries_with_images = [entry for entry in animal_entries if entry.image_url]
        
        if not entries_with_images:
            logger.info("No images to download")
            return animal_entries
        
        # Create semaphore to limit concurrent downloads
        semaphore = asyncio.Semaphore(self.config.max_concurrent_downloads)
        
        async def download_with_semaphore(session: aiohttp.ClientSession, entry: AnimalEntry) -> AnimalEntry:
            async with semaphore:
                return await self.image_downloader.download_image(session, entry)
        
        # Download images concurrently with limited concurrency
        connector = aiohttp.TCPConnector(limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
        
        async with aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout,
            headers={'User-Agent': 'AnimalScraper/1.0 (Educational Purpose)'}
        ) as session:
            tasks = [download_with_semaphore(session, entry) for entry in entries_with_images]
            updated_entries = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Replace entries with updated versions, handling exceptions
        entry_map = {}
        for i, result in enumerate(updated_entries):
            if not isinstance(result, Exception):
                key = entries_with_images[i].animal_name + entries_with_images[i].collateral_adjective
                entry_map[key] = result
        
        # Update the original list of animal entries
        for i, entry in enumerate(animal_entries):
            key = entry.animal_name + entry.collateral_adjective
            if key in entry_map:
                animal_entries[i] = entry_map[key]
        
        images_downloaded = sum(1 for entry in animal_entries if entry.local_image_path)
        logger.info(f"Successfully downloaded {images_downloaded} images")
        
        return animal_entries
