
import pytest
from src.core.parser import AnimalDataParser
from src.core.models import AnimalEntry, ScrapingConfig, get_default_tmp_dir
from pydantic import ValidationError
from pathlib import Path
from unittest.mock import AsyncMock

from src.core.scraper import AnimalScraper
from src.core.models import AnimalEntry

@pytest.fixture
def parser():
    return AnimalDataParser()

def test_multiple_adjectives(parser):
    html = """
    <table class="wikitable">
        <tr><th>Animal</th><th>Collateral adjective</th></tr>
        <tr><td><a href="/wiki/Wolf">Wolf</a></td><td>wolfish, lupine</td></tr>
    </table>
    """
    result = parser.parse_wikipedia_page(html)
    assert ("Wolf", "wolfish", ["https://en.wikipedia.org/wiki/Wolf"]) in result
    assert ("Wolf", "lupine", ["https://en.wikipedia.org/wiki/Wolf"]) in result
    assert len(result) == 2


def test_model_validation_and_config_defaults():
    
    entry = AnimalEntry(
        animal_name="Tiger",
        collateral_adjective="Tigroid",
        image_url="https://example.com/tiger.jpg",
        local_image_path="/tmp/tiger.jpg"
    )
    assert entry.animal_name == "Tiger"
    assert entry.collateral_adjective == "Tigroid"

    with pytest.raises(ValidationError):
        AnimalEntry(animal_name="", collateral_adjective="  ")

    
    config = ScrapingConfig()
    assert config.base_url == "https://en.wikipedia.org/wiki/List_of_animal_names"
    assert isinstance(config.image_dir, Path)
    assert config.image_dir.exists()
    assert config.max_concurrent_downloads == 10
    assert config.request_timeout == 30

    tmp_path = get_default_tmp_dir()
    assert tmp_path.name == "animal_images"


@pytest.mark.asyncio
async def test_create_animal_entries_basic():
    scraper = AnimalScraper()
    
    scraper.image_finder.find_image_from_url_async = AsyncMock(return_value="https://example.com/image.jpg")
    scraper.image_finder.find_animal_image = AsyncMock(return_value="https://example.com/fallback.jpg")
    
    
    data_list = [
        ("Cat", "feline", ["https://en.wikipedia.org/wiki/Cat"]),
        ("Dog", "canine", ["https://en.wikipedia.org/wiki/Dog"]),
    ]
    
    entries = await scraper._create_animal_entries(data_list)
    
    assert len(entries) == 2
    for entry in entries:
        assert isinstance(entry, AnimalEntry)
        assert entry.animal_name in ["Cat", "Dog"]
        assert entry.collateral_adjective in ["feline", "canine"]
        # התמונה צריכה להיות כתובת שהמוק מחזיר
        assert entry.image_url == "https://example.com/image.jpg"
