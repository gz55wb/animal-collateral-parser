import tempfile
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional
from pathlib import Path


 #Pydantic Models for Data Validation
class AnimalEntry(BaseModel):
    """Represents a single animal entry with its collateral adjective(s)."""
    
    animal_name: str = Field(..., min_length=1, description="Name of the animal")
    collateral_adjective: str = Field(..., min_length=1, description="Collateral adjective")
    image_url: Optional[HttpUrl] = Field(None, description="URL to animal image")
    local_image_path: Optional[str] = Field(None, description="Local path to downloaded image")
    
    @validator('animal_name', 'collateral_adjective')
    def validate_non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError('Value cannot be empty or whitespace only')
        return v.strip()

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        str_strip_whitespace = True

def get_default_tmp_dir() -> Path:
    return Path(tempfile.gettempdir()) / "animal_images"

class ScrapingConfig(BaseModel):
    """Configuration for the scraping operation."""
    
    base_url: HttpUrl = Field(
        default="https://en.wikipedia.org/wiki/List_of_animal_names",
        description="URL to scrape"
    )
    image_dir: Path = Field(
        default_factory =get_default_tmp_dir,
        description="Directory to store downloaded images"
    )
    output_file: Path = Field(
        default=Path("animal_report.html"),
        description="Output HTML file path"
    )
    max_concurrent_downloads: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum concurrent image downloads"
    )
    request_timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Request timeout in seconds"
    )
    
    @validator('image_dir', 'output_file')
    def convert_to_path(cls, v):
        return Path(v) if not isinstance(v, Path) else v
    
    def __init__(self, **data):
        super().__init__(**data)
        
        if not self.image_dir.exists():
            self.image_dir.mkdir(parents=True, exist_ok=True)