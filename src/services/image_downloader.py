import re
import aiohttp
from src.core.models import AnimalEntry, ScrapingConfig
from typing import Set
from urllib.parse import urlparse
import hashlib
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ImageDownloader:
    """Handles asynchronous downloading of animal images."""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.downloaded_files: Set[str] = set()
    
    async def download_image(self, session: aiohttp.ClientSession, animal_entry: AnimalEntry) -> AnimalEntry:
        """
        Download an image for an animal entry.
        
        Args:
            session: aiohttp session for downloading
            animal_entry: AnimalEntry to download image for
            
        Returns:
            Updated AnimalEntry with local image path
        """
        if not animal_entry.image_url:
            return animal_entry
        
        try:
            # Create a safe filename
            safe_name = re.sub(r'[^\w\-_.]', '_', animal_entry.animal_name)
            file_extension = self._get_file_extension(str(animal_entry.image_url))
            filename = f"{safe_name}_{hashlib.md5(str(animal_entry.image_url).encode()).hexdigest()[:8]}{file_extension}"
            file_path = self.config.image_dir / filename
            
            # Skip if already downloaded
            if filename in self.downloaded_files:
                animal_entry.local_image_path = str(file_path)
                return animal_entry
            
            async with session.get(str(animal_entry.image_url), timeout=self.config.request_timeout) as response:
                if response.status == 200:
                    content = await response.read()
                    file_path.write_bytes(content)
                    self.downloaded_files.add(filename)
                    animal_entry.local_image_path = str(file_path)
                    logger.debug(f"Downloaded image for {animal_entry.animal_name}")
                else:
                    logger.warning(f"Failed to download image for {animal_entry.animal_name}: HTTP {response.status}")
        
        except Exception as e:
            logger.warning(f"Error downloading image for {animal_entry.animal_name}: {str(e)}")
        
        return animal_entry
    
    def _get_file_extension(self, url: str) -> str:
        """Extract file extension from URL."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        if '.jpg' in path or '.jpeg' in path:
            return '.jpg'
        elif '.png' in path:
            return '.png'
        elif '.svg' in path:
            return '.svg'
        else:
            return '.jpg'  # Default fallback