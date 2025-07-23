import pytest
from src.core.parser import AnimalDataParser
from src.core.models import AnimalEntry, ScrapingConfig, get_default_tmp_dir
from pydantic import ValidationError
from pathlib import Path
from unittest.mock import AsyncMock

from src.core.scraper import AnimalScraper
from src.core.models import AnimalEntry
from src.utils.config_loader import load_config

@pytest.fixture
def parser():
    """Fixture to instantiate the AnimalDataParser."""
    return AnimalDataParser()

def test_multiple_adjectives(parser):
    """
    Test that multiple collateral adjectives for a single animal are correctly parsed,
    and that each adjective results in a separate tuple with the animal and links.
    """
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
    """
    Test AnimalEntry model validation and default ScrapingConfig values.
    Validates:
    - Proper field values are accepted.
    - Empty or whitespace-only strings raise ValidationError.
    - ScrapingConfig default values and directories are correctly set.
    """
    
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
    """
    Test async creation of AnimalEntry objects, mocking image fetching methods.
    Ensures that entries are correctly created with expected values.
    """
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
        assert entry.image_url == "https://example.com/image.jpg"

def test_config_keywords():
    """
    Test that the loaded configuration contains expected keywords
    and that they are lists.
    """
    config = load_config()
    assert "collateral_keywords" in config
    assert "trivial_name_keywords" in config
    assert isinstance(config["collateral_keywords"], list)
    assert isinstance(config["trivial_name_keywords"], list)
