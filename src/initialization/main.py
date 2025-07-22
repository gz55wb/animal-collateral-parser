# """
# Professional Animal Names and Collateral Adjectives Scraper
# ==========================================================

# A production-level Python application that scrapes Wikipedia's list of animal names,
# extracts collateral adjectives, downloads animal images, and generates HTML reports.

# Author: Raz Zorno
# Date: July 2025
# """

# import asyncio
# import logging
# import time
# from dataclasses import dataclass, field
# from pathlib import Path
# from typing import Dict, List, Optional, Set, Tuple, Union
# from urllib.parse import urljoin, urlparse
# import hashlib
# import re

# import aiohttp
# import requests
# from bs4 import BeautifulSoup, Tag
# from pydantic import BaseModel, Field, HttpUrl, validator
# import pytest


# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)


# # Pydantic Models for Data Validation
# class AnimalEntry(BaseModel):
#     """Represents a single animal entry with its collateral adjective(s)."""
    
#     animal_name: str = Field(..., min_length=1, description="Name of the animal")
#     collateral_adjective: str = Field(..., min_length=1, description="Collateral adjective")
#     image_url: Optional[HttpUrl] = Field(None, description="URL to animal image")
#     local_image_path: Optional[str] = Field(None, description="Local path to downloaded image")
    
#     @validator('animal_name', 'collateral_adjective')
#     def validate_non_empty_strings(cls, v):
#         if not v or not v.strip():
#             raise ValueError('Value cannot be empty or whitespace only')
#         return v.strip()

#     class Config:
#         """Pydantic configuration."""
#         validate_assignment = True
#         str_strip_whitespace = True


# class ScrapingConfig(BaseModel):
#     """Configuration for the scraping operation."""
    
#     base_url: HttpUrl = Field(
#         default="https://en.wikipedia.org/wiki/List_of_animal_names",
#         description="URL to scrape"
#     )
#     image_dir: Path = Field(
#         default=Path("/tmp/animal_images"),
#         description="Directory to store downloaded images"
#     )
#     output_file: Path = Field(
#         default=Path("animal_report.html"),
#         description="Output HTML file path"
#     )
#     max_concurrent_downloads: int = Field(
#         default=10,
#         ge=1,
#         le=50,
#         description="Maximum concurrent image downloads"
#     )
#     request_timeout: int = Field(
#         default=30,
#         ge=5,
#         le=120,
#         description="Request timeout in seconds"
#     )
    
#     @validator('image_dir', 'output_file')
#     def convert_to_path(cls, v):
#         return Path(v) if not isinstance(v, Path) else v


# # Decorators
# def timing_decorator(func):
#     """Decorator to measure execution time of functions."""
#     def wrapper(*args, **kwargs):
#         start_time = time.time()
#         try:
#             result = func(*args, **kwargs)
#             execution_time = time.time() - start_time
#             logger.info(f"{func.__name__} completed in {execution_time:.2f} seconds")
#             return result
#         except Exception as e:
#             execution_time = time.time() - start_time
#             logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds: {str(e)}")
#             raise
#     return wrapper


# def retry_decorator(max_retries: int = 3, delay: float = 1.0):
#     """Decorator to retry failed operations."""
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             last_exception = None
#             for attempt in range(max_retries):
#                 try:
#                     return func(*args, **kwargs)
#                 except Exception as e:
#                     last_exception = e
#                     if attempt < max_retries - 1:
#                         logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {delay}s...")
#                         time.sleep(delay)
#                     else:
#                         logger.error(f"All {max_retries} attempts failed for {func.__name__}")
#             raise last_exception
#         return wrapper
#     return decorator


# def error_handler_decorator(default_return=None):
#     """Decorator to handle and log errors gracefully."""
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             try:
#                 return func(*args, **kwargs)
#             except Exception as e:
#                 logger.error(f"Error in {func.__name__}: {str(e)}")
#                 return default_return
#         return wrapper
#     return decorator


# # Core Classes
# class WikipediaImageFinder:
#     """Handles finding and extracting image URLs from Wikipedia pages."""
    
#     def __init__(self, session: Optional[requests.Session] = None):
#         self.session = session or requests.Session()
#         self.session.headers.update({
#             'User-Agent': 'AnimalScraper/1.0 (Educational Purpose)'
#         })
    
#     @retry_decorator(max_retries=2)
#     @error_handler_decorator(default_return=None)
#     def find_animal_image(self, animal_name: str) -> Optional[str]:
#         """
#         Find an image URL for a given animal by searching Wikipedia.
        
#         Args:
#             animal_name: Name of the animal to search for
            
#         Returns:
#             Image URL if found, None otherwise
#         """
#         try:
#             # Search for the animal's Wikipedia page
#             search_url = f"https://en.wikipedia.org/wiki/{animal_name.replace(' ', '_')}"
#             response = self.session.get(search_url, timeout=10)
            
#             if response.status_code != 200:
#                 return None
            
#             soup = BeautifulSoup(response.content, 'html.parser')
            
#             # Look for the main infobox image
#             infobox = soup.find('table', class_='infobox')
#             if infobox:
#                 img_tag = infobox.find('img')
#                 if img_tag and img_tag.get('src'):
#                     img_url = img_tag['src']
#                     if img_url.startswith('//'):
#                         img_url = 'https:' + img_url
#                     return img_url
            
#             # Fallback: look for any image in the content
#             content_images = soup.find_all('img', limit=5)
#             for img in content_images:
#                 src = img.get('src', '')
#                 if any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.svg']):
#                     if 'commons' in src or 'upload' in src:
#                         if src.startswith('//'):
#                             src = 'https:' + src
#                         return src
            
#             return None
#         except Exception as e:
#             logger.debug(f"Error finding image for {animal_name}: {str(e)}")
#             return None


# class ImageDownloader:
#     """Handles asynchronous downloading of animal images."""
    
#     def __init__(self, config: ScrapingConfig):
#         self.config = config
#         self.downloaded_files: Set[str] = set()
    
#     async def download_image(self, session: aiohttp.ClientSession, animal_entry: AnimalEntry) -> AnimalEntry:
#         """
#         Download an image for an animal entry.
        
#         Args:
#             session: aiohttp session for downloading
#             animal_entry: AnimalEntry to download image for
            
#         Returns:
#             Updated AnimalEntry with local image path
#         """
#         if not animal_entry.image_url:
#             return animal_entry
        
#         try:
#             # Create a safe filename
#             safe_name = re.sub(r'[^\w\-_.]', '_', animal_entry.animal_name)
#             file_extension = self._get_file_extension(str(animal_entry.image_url))
#             filename = f"{safe_name}_{hashlib.md5(str(animal_entry.image_url).encode()).hexdigest()[:8]}{file_extension}"
#             file_path = self.config.image_dir / filename
            
#             # Skip if already downloaded
#             if filename in self.downloaded_files:
#                 animal_entry.local_image_path = str(file_path)
#                 return animal_entry
            
#             async with session.get(str(animal_entry.image_url), timeout=self.config.request_timeout) as response:
#                 if response.status == 200:
#                     content = await response.read()
#                     file_path.write_bytes(content)
#                     self.downloaded_files.add(filename)
#                     animal_entry.local_image_path = str(file_path)
#                     logger.debug(f"Downloaded image for {animal_entry.animal_name}")
#                 else:
#                     logger.warning(f"Failed to download image for {animal_entry.animal_name}: HTTP {response.status}")
        
#         except Exception as e:
#             logger.warning(f"Error downloading image for {animal_entry.animal_name}: {str(e)}")
        
#         return animal_entry
    
#     def _get_file_extension(self, url: str) -> str:
#         """Extract file extension from URL."""
#         parsed = urlparse(url)
#         path = parsed.path.lower()
#         if '.jpg' in path or '.jpeg' in path:
#             return '.jpg'
#         elif '.png' in path:
#             return '.png'
#         elif '.svg' in path:
#             return '.svg'
#         else:
#             return '.jpg'  # Default fallback


# class AnimalDataParser:
#     """Parses Wikipedia page to extract animal names and collateral adjectives."""
    
#     @timing_decorator
#     def parse_wikipedia_page(self, html_content: str) -> List[Tuple[str, str]]:
#         """
#         Parse the Wikipedia page to extract animal-adjective pairs.
        
#         Args:
#             html_content: HTML content of the Wikipedia page
            
#         Returns:
#             List of (animal_name, collateral_adjective) tuples
#         """
#         soup = BeautifulSoup(html_content, 'html.parser')
#         animal_adjective_pairs = []
        
#         # Find all tables that might contain the data
#         tables = soup.find_all('table', class_='wikitable')
        
#         for table in tables:
#             rows = table.find_all('tr')[1:]  # Skip header row
            
#             for row in rows:
#                 cells = row.find_all(['td', 'th'])
#                 if len(cells) >= 2:
#                     # Extract animal name (usually first column)
#                     animal_cell = cells[0]
#                     animal_name = self._extract_text_from_cell(animal_cell)
                    
#                     if not animal_name:
#                         continue
                    
#                     # Look for collateral adjective in subsequent columns
#                     for cell in cells[1:]:
#                         adjective = self._extract_text_from_cell(cell)
#                         if adjective and self._is_likely_adjective(adjective):
#                             # Handle multiple adjectives separated by commas
#                             adjectives = [adj.strip() for adj in adjective.split(',')]
#                             for adj in adjectives:
#                                 if adj and self._is_likely_adjective(adj):
#                                     animal_adjective_pairs.append((animal_name, adj))
#                             break
        
#         logger.info(f"Extracted {len(animal_adjective_pairs)} animal-adjective pairs")
#         return animal_adjective_pairs
    
#     def _extract_text_from_cell(self, cell: Tag) -> str:
#         """Extract clean text from a table cell."""
#         # Remove reference markers and extra whitespace
#         text = cell.get_text(strip=True)
#         # Remove citation markers like [1], [2], etc.
#         text = re.sub(r'\[\d+\]', '', text)
#         # Remove parenthetical content that might be scientific names
#         text = re.sub(r'\([^)]*\)', '', text)
#         return text.strip()
    
#     def _is_likely_adjective(self, text: str) -> bool:
#         """Check if text is likely a collateral adjective."""
#         if not text or len(text) < 2:
#             return False
        
#         # Filter out common non-adjective patterns
#         exclude_patterns = [
#             r'^\d+$',  # Just numbers
#             r'^[A-Z]{2,}$',  # All caps abbreviations
#             r'species$',  # Ends with 'species'
#             r'animal$',  # Ends with 'animal'
#         ]
        
#         for pattern in exclude_patterns:
#             if re.match(pattern, text, re.IGNORECASE):
#                 return False
        
#         return True


# class HTMLReportGenerator:
#     """Generates HTML reports for the scraped data."""
    
#     def __init__(self, config: ScrapingConfig):
#         self.config = config
    
#     @timing_decorator
#     def generate_report(self, animal_entries: List[AnimalEntry], execution_time: float) -> Path:
#         """
#         Generate an HTML report of the scraped data.
        
#         Args:
#             animal_entries: List of AnimalEntry objects
#             execution_time: Total execution time in seconds
            
#         Returns:
#             Path to the generated HTML file
#         """
#         html_content = self._build_html_content(animal_entries, execution_time)
        
#         self.config.output_file.write_text(html_content, encoding='utf-8')
#         logger.info(f"HTML report generated: {self.config.output_file}")
        
#         return self.config.output_file
    
#     def _build_html_content(self, animal_entries: List[AnimalEntry], execution_time: float) -> str:
#         """Build the complete HTML content."""
#         stats = self._calculate_statistics(animal_entries)
        
#         html = f"""
#         <!DOCTYPE html>
#         <html lang="en">
#         <head>
#             <meta charset="UTF-8">
#             <meta name="viewport" content="width=device-width, initial-scale=1.0">
#             <title>Animal Names and Collateral Adjectives Report</title>
#             <style>
#                 {self._get_css_styles()}
#             </style>
#         </head>
#         <body>
#             <header>
#                 <h1>Animal Names and Collateral Adjectives</h1>
#                 <p class="subtitle">Scraped from Wikipedia's List of Animal Names</p>
#             </header>
            
#             <div class="stats">
#                 <div class="stat-card">
#                     <h3>Total Entries</h3>
#                     <p class="stat-number">{stats['total_entries']}</p>
#                 </div>
#                 <div class="stat-card">
#                     <h3>Unique Animals</h3>
#                     <p class="stat-number">{stats['unique_animals']}</p>
#                 </div>
#                 <div class="stat-card">
#                     <h3>Unique Adjectives</h3>
#                     <p class="stat-number">{stats['unique_adjectives']}</p>
#                 </div>
#                 <div class="stat-card">
#                     <h3>Images Downloaded</h3>
#                     <p class="stat-number">{stats['images_downloaded']}</p>
#                 </div>
#                 <div class="stat-card">
#                     <h3>Execution Time</h3>
#                     <p class="stat-number">{execution_time:.1f}s</p>
#                 </div>
#             </div>
            
#             <div class="content">
#                 <h2>Animal Entries ({len(animal_entries)} total)</h2>
#                 <div class="animal-grid">
#                     {self._build_animal_cards(animal_entries)}
#                 </div>
#             </div>
            
#             <footer>
#                 <p>Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
#             </footer>
#         </body>
#         </html>
#         """
#         return html
    
#     def _calculate_statistics(self, animal_entries: List[AnimalEntry]) -> Dict[str, int]:
#         """Calculate statistics for the report."""
#         unique_animals = set(entry.animal_name for entry in animal_entries)
#         unique_adjectives = set(entry.collateral_adjective for entry in animal_entries)
#         images_downloaded = sum(1 for entry in animal_entries if entry.local_image_path)
        
#         return {
#             'total_entries': len(animal_entries),
#             'unique_animals': len(unique_animals),
#             'unique_adjectives': len(unique_adjectives),
#             'images_downloaded': images_downloaded,
#         }
    
#     def _build_animal_cards(self, animal_entries: List[AnimalEntry]) -> str:
#         """Build HTML cards for animal entries."""
#         cards = []
#         for entry in animal_entries:
#             image_html = ""
#             if entry.local_image_path and Path(entry.local_image_path).exists():
#                 image_html = f'<img src="file://{entry.local_image_path}" alt="{entry.animal_name}" class="animal-image">'
            
#             card = f"""
#             <div class="animal-card">
#                 {image_html}
#                 <div class="animal-info">
#                     <h3 class="animal-name">{entry.animal_name}</h3>
#                     <p class="adjective">Collateral adjective: <em>{entry.collateral_adjective}</em></p>
#                 </div>
#             </div>
#             """
#             cards.append(card)
        
#         return ''.join(cards)
    
#     def _get_css_styles(self) -> str:
#         """Return CSS styles for the HTML report."""
#         return """
#         * {
#             margin: 0;
#             padding: 0;
#             box-sizing: border-box;
#         }
        
#         body {
#             font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
#             line-height: 1.6;
#             color: #333;
#             background-color: #f5f5f5;
#         }
        
#         header {
#             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#             color: white;
#             text-align: center;
#             padding: 2rem 1rem;
#             margin-bottom: 2rem;
#         }
        
#         h1 {
#             font-size: 2.5rem;
#             margin-bottom: 0.5rem;
#         }
        
#         .subtitle {
#             font-size: 1.1rem;
#             opacity: 0.9;
#         }
        
#         .stats {
#             display: grid;
#             grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
#             gap: 1rem;
#             max-width: 1200px;
#             margin: 0 auto 2rem auto;
#             padding: 0 1rem;
#         }
        
#         .stat-card {
#             background: white;
#             padding: 1.5rem;
#             border-radius: 10px;
#             text-align: center;
#             box-shadow: 0 2px 10px rgba(0,0,0,0.1);
#         }
        
#         .stat-card h3 {
#             color: #666;
#             font-size: 0.9rem;
#             text-transform: uppercase;
#             letter-spacing: 1px;
#             margin-bottom: 0.5rem;
#         }
        
#         .stat-number {
#             font-size: 2rem;
#             font-weight: bold;
#             color: #667eea;
#         }
        
#         .content {
#             max-width: 1200px;
#             margin: 0 auto;
#             padding: 0 1rem;
#         }
        
#         .content h2 {
#             margin-bottom: 1.5rem;
#             color: #333;
#         }
        
#         .animal-grid {
#             display: grid;
#             grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
#             gap: 1.5rem;
#             margin-bottom: 3rem;
#         }
        
#         .animal-card {
#             background: white;
#             border-radius: 10px;
#             overflow: hidden;
#             box-shadow: 0 4px 15px rgba(0,0,0,0.1);
#             transition: transform 0.2s ease, box-shadow 0.2s ease;
#         }
        
#         .animal-card:hover {
#             transform: translateY(-5px);
#             box-shadow: 0 8px 25px rgba(0,0,0,0.15);
#         }
        
#         .animal-image {
#             width: 100%;
#             height: 200px;
#             object-fit: cover;
#             border-bottom: 1px solid #eee;
#         }
        
#         .animal-info {
#             padding: 1.5rem;
#         }
        
#         .animal-name {
#             font-size: 1.3rem;
#             margin-bottom: 0.5rem;
#             color: #333;
#         }
        
#         .adjective {
#             color: #666;
#             font-size: 0.95rem;
#         }
        
#         .adjective em {
#             color: #667eea;
#             font-weight: 600;
#         }
        
#         footer {
#             text-align: center;
#             padding: 2rem;
#             color: #666;
#             font-size: 0.9rem;
#         }
        
#         @media (max-width: 768px) {
#             h1 {
#                 font-size: 2rem;
#             }
            
#             .stats {
#                 grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
#             }
            
#             .animal-grid {
#                 grid-template-columns: 1fr;
#             }
#         }
#         """


# class AnimalScraper:
#     """Main scraper class that orchestrates the entire operation."""
    
#     def __init__(self, config: Optional[ScrapingConfig] = None):
#         self.config = config or ScrapingConfig()
#         self.parser = AnimalDataParser()
#         self.image_finder = WikipediaImageFinder()
#         self.image_downloader = ImageDownloader(self.config)
#         self.report_generator = HTMLReportGenerator(self.config)
        
#         # Ensure image directory exists
#         self.config.image_dir.mkdir(parents=True, exist_ok=True)
    
#     @timing_decorator
#     async def scrape_and_generate_report(self) -> Tuple[List[AnimalEntry], Path, float]:
#         """
#         Main method to scrape data and generate report.
        
#         Returns:
#             Tuple of (animal_entries, report_path, execution_time)
#         """
#         start_time = time.time()
        
#         try:
#             # Step 1: Fetch and parse Wikipedia page
#             logger.info("Fetching Wikipedia page...")
#             html_content = self._fetch_wikipedia_page()
            
#             # Step 2: Extract animal-adjective pairs
#             logger.info("Parsing animal data...")
#             animal_adjective_pairs = self.parser.parse_wikipedia_page(html_content)
            
#             if not animal_adjective_pairs:
#                 raise ValueError("No animal-adjective pairs found on the page")
            
#             # Step 3: Create AnimalEntry objects and find images
#             logger.info("Creating animal entries and finding images...")
#             animal_entries = await self._create_animal_entries(animal_adjective_pairs)
            
#             # Step 4: Download images
#             logger.info("Downloading images...")
#             animal_entries = await self._download_images(animal_entries)
            
#             # Step 5: Generate HTML report
#             execution_time = time.time() - start_time
#             logger.info("Generating HTML report...")
#             report_path = self.report_generator.generate_report(animal_entries, execution_time)
            
#             logger.info(f"Scraping completed successfully in {execution_time:.2f} seconds")
#             logger.info(f"Found {len(animal_entries)} animal entries")
#             logger.info(f"Report saved to: {report_path}")
            
#             return animal_entries, report_path, execution_time
            
#         except Exception as e:
#             execution_time = time.time() - start_time
#             logger.error(f"Scraping failed after {execution_time:.2f} seconds: {str(e)}")
#             raise
    
#     @retry_decorator(max_retries=3, delay=2.0)
#     def _fetch_wikipedia_page(self) -> str:
#         """Fetch the Wikipedia page content."""
#         response = requests.get(
#             str(self.config.base_url),
#             timeout=self.config.request_timeout,
#             headers={'User-Agent': 'AnimalScraper/1.0 (Educational Purpose)'}
#         )
#         response.raise_for_status()
#         return response.text
    
#     async def _create_animal_entries(self, pairs: List[Tuple[str, str]]) -> List[AnimalEntry]:
#         """Create AnimalEntry objects and find images for them."""
#         entries = []
#         processed_animals = set()
        
#         for animal_name, adjective in pairs:
#             try:
#                 # Find image URL if we haven't processed this animal yet
#                 image_url = None
#                 if animal_name not in processed_animals:
#                     image_url = self.image_finder.find_animal_image(animal_name)
#                     processed_animals.add(animal_name)
                
#                 entry = AnimalEntry(
#                     animal_name=animal_name,
#                     collateral_adjective=adjective,
#                     image_url=image_url
#                 )
#                 entries.append(entry)
                
#             except Exception as e:
#                 logger.warning(f"Error creating entry for {animal_name}: {str(e)}")
#                 continue
        
#         return entries
    
#     async def _download_images(self, animal_entries: List[AnimalEntry]) -> List[AnimalEntry]:
#         """Download images for all animal entries."""
#         # Filter entries that have image URLs
#         entries_with_images = [entry for entry in animal_entries if entry.image_url]
        
#         if not entries_with_images:
#             logger.info("No images to download")
#             return animal_entries
        
#         # Create semaphore to limit concurrent downloads
#         semaphore = asyncio.Semaphore(self.config.max_concurrent_downloads)
        
#         async def download_with_semaphore(session: aiohttp.ClientSession, entry: AnimalEntry) -> AnimalEntry:
#             async with semaphore:
#                 return await self.image_downloader.download_image(session, entry)
        
#         # Download images concurrently
#         connector = aiohttp.TCPConnector(limit_per_host=5)
#         timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
        
#         async with aiohttp.ClientSession(
#             connector=connector, 
#             timeout=timeout,
#             headers={'User-Agent': 'AnimalScraper/1.0 (Educational Purpose)'}
#         ) as session:
#             tasks = [download_with_semaphore(session, entry) for entry in entries_with_images]
#             updated_entries = await asyncio.gather(*tasks, return_exceptions=True)
        
#         # Replace entries with updated versions (handle exceptions)
#         entry_map = {}
#         for i, result in enumerate(updated_entries):
#             if not isinstance(result, Exception):
#                 entry_map[entries_with_images[i].animal_name + entries_with_images[i].collateral_adjective] = result
        
#         # Update original list
#         for i, entry in enumerate(animal_entries):
#             key = entry.animal_name + entry.collateral_adjective
#             if key in entry_map:
#                 animal_entries[i] = entry_map[key]
        
#         images_downloaded = sum(1 for entry in animal_entries if entry.local_image_path)
#         logger.info(f"Successfully downloaded {images_downloaded} images")
        
#         return animal_entries


# # Multi-user support (if needed for production deployment)
# class UserSession:
#     """Handles user-specific scraping sessions for multi-user support."""
    
#     def __init__(self, user_id: str, config: Optional[ScrapingConfig] = None):
#         self.user_id = user_id
#         self.config = config or ScrapingConfig()
        
#         # Create user-specific directories
#         user_dir = Path(f"/tmp/animal_scraper_user_{user_id}")
#         self.config.image_dir = user_dir / "images"
#         self.config.output_file = user_dir / "report.html"
        
#         user_dir.mkdir(parents=True, exist_ok=True)
#         self.config.image_dir.mkdir(parents=True, exist_ok=True)
        
#         self.scraper = AnimalScraper(self.config)
    
#     async def run_scraping_session(self) -> Tuple[List[AnimalEntry], Path, float]:
#         """Run a scraping session for this user."""
#         logger.info(f"Starting scraping session for user {self.user_id}")
#         return await self.scraper.scrape_and_generate_report()


# # Test Cases
# class TestAnimalScraper:
#     """Test cases for the AnimalScraper application."""
    
#     @pytest.fixture
#     def sample_html(self):
#         """Sample HTML content for testing."""
#         return """
#         <html>
#         <body>
#             <table class="wikitable">
#                 <tr><th>Animal</th><th>Collateral adjective</th></tr>
#                 <tr><td>Dog</td><td>Canine</td></tr>
#                 <tr><td>Cat</td><td>Feline</td></tr>
#                 <tr><td>Horse</td><td>Equine, equestrian</td></tr>
#             </table>
#         </body>
#         </html>
#         """
    
#     @pytest.fixture
#     def config(self):
#         """Test configuration."""
#         return ScrapingConfig(
#             image_dir=Path("/tmp/test_images"),
#             output_file=Path("/tmp/test_report.html")
#         )
    
#     def test_animal_entry_validation(self):
#         """Test AnimalEntry Pydantic validation."""
#         # Valid entry
#         entry = AnimalEntry(animal_name="Dog", collateral_adjective="Canine")
#         assert entry.animal_name == "Dog"
#         assert entry.collateral_adjective == "Canine"
        
#         # Test validation errors
#         with pytest.raises(ValueError):
#             AnimalEntry(animal_name="", collateral_adjective="Canine")
        
#         with pytest.raises(ValueError):
#             AnimalEntry(animal_name="Dog", collateral_adjective="   ")
    
#     def test_parser_extraction(self, sample_html):
#         """Test parsing of HTML content."""
#         parser = AnimalDataParser()
#         pairs = parser.parse_wikipedia_page(sample_html)
        
#         assert len(pairs) >= 3
#         assert ("Dog", "Canine") in pairs
#         assert ("Cat", "Feline") in pairs
#         assert ("Horse", "Equine") in pairs
#         assert ("Horse", "equestrian") in pairs
    
#     def test_is_likely_adjective(self):
#         """Test adjective validation logic."""
#         parser = AnimalDataParser()
        
#         # Valid adjectives
#         assert parser._is_likely_adjective("feline")
#         assert parser._is_



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
