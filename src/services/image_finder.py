import requests
from bs4 import BeautifulSoup
from typing import Optional
from src.utils.logger import get_logger
from src.utils.decorators import retry_decorator, error_handler_decorator

logger = get_logger(__name__)

# Core Classes
class WikipediaImageFinder:
    """Handles finding and extracting image URLs from Wikipedia pages."""
    
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update({
            'User-Agent': 'AnimalScraper/1.0 (Educational Purpose)'
        })
    
    @retry_decorator(max_retries=2)
    @error_handler_decorator(default_return=None)
    def find_animal_image(self, animal_name: str) -> Optional[str]:
        """
        Find an image URL for a given animal by searching Wikipedia.
        
        Args:
            animal_name: Name of the animal to search for
            
        Returns:
            Image URL if found, None otherwise
        """
        try:
            # Search for the animal's Wikipedia page
            search_url = f"https://en.wikipedia.org/wiki/{animal_name.replace(' ', '_')}"
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the main infobox image
            infobox = soup.find('table', class_='infobox')
            if infobox:
                img_tag = infobox.find('img')
                if img_tag and img_tag.get('src'):
                    img_url = img_tag['src']
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    return img_url
            
            # Fallback: look for any image in the content
            content_images = soup.find_all('img', limit=5)
            for img in content_images:
                src = img.get('src', '')
                if any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.svg']):
                    if 'commons' in src or 'upload' in src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        return src
            
            return None
        except Exception as e:
            logger.debug(f"Error finding image for {animal_name}: {str(e)}")
            return None