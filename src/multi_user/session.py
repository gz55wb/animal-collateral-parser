from core.models import AnimalEntry, ScrapingConfig
from typing import Optional, Tuple, List
from core.scraper import AnimalScraper
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


# Multi-user support (if needed for production deployment)
class UserSession:
    """Handles user-specific scraping sessions for multi-user support."""
    
    def __init__(self, user_id: str, config: Optional[ScrapingConfig] = None):
        self.user_id = user_id
        self.config = config or ScrapingConfig()
        
        # Create user-specific directories
        user_dir = Path(f"/tmp/animal_scraper_user_{user_id}")
        self.config.image_dir = user_dir / "images"
        self.config.output_file = user_dir / "report.html"
        
        user_dir.mkdir(parents=True, exist_ok=True)
        self.config.image_dir.mkdir(parents=True, exist_ok=True)
        
        self.scraper = AnimalScraper(self.config)
    
    async def run_scraping_session(self) -> Tuple[List[AnimalEntry], Path, float]:
        """Run a scraping session for this user."""
        logger.info(f"Starting scraping session for user {self.user_id}")
        return await self.scraper.scrape_and_generate_report()