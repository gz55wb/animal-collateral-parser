import tempfile
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional
from pathlib import Path


# Pydantic Models for Data Validation
class AnimalEntry(BaseModel):
    """
    Represents a single animal entry with its collateral adjective(s) and optional image information.
    
    Attributes:
        animal_name (str): Name of the animal.
        collateral_adjective (str): Collateral adjective related to the animal.
        image_url (Optional[HttpUrl]): URL to the animal's image.
        local_image_path (Optional[str]): Local filesystem path to the downloaded image.
    """
    
    animal_name: str = Field(..., min_length=1, description="Name of the animal")
    collateral_adjective: str = Field(..., min_length=1, description="Collateral adjective")
    image_url: Optional[HttpUrl] = Field(None, description="URL to animal image")
    local_image_path: Optional[str] = Field(None, description="Local path to downloaded image")
    
    @validator('animal_name', 'collateral_adjective')
    def validate_non_empty_strings(cls, v):
        """
        Validator to ensure that 'animal_name' and 'collateral_adjective' are not empty or whitespace only.
        
        Args:
            v (str): The string value to validate.
            
        Returns:
            str: Stripped string if valid.
            
        Raises:
            ValueError: If the value is empty or contains only whitespace.
        """
        if not v or not v.strip():
            raise ValueError('Value cannot be empty or whitespace only')
        return v.strip()

    class Config:
        """Pydantic configuration to validate assignments and strip whitespace automatically."""
        validate_assignment = True
        str_strip_whitespace = True


def get_default_tmp_dir() -> Path:
    """
    Returns the default temporary directory path for storing animal images.
    This directory is a subdirectory 'animal_images' inside the system temp folder.
    
    Returns:
        Path: The path to the default temporary image directory.
    """
    return Path(tempfile.gettempdir()) / "animal_images"


class ScrapingConfig(BaseModel):
    """
    Configuration model for the scraping operation.
    
    Attributes:
        base_url (HttpUrl): URL to scrape animal data from.
        image_dir (Path): Directory to store downloaded images.
        output_file (Path): Path for the output HTML report file.
        max_concurrent_downloads (int): Maximum number of concurrent image downloads allowed.
        request_timeout (int): Timeout in seconds for HTTP requests.
    """
    
    base_url: HttpUrl = Field(
        default="https://en.wikipedia.org/wiki/List_of_animal_names",
        description="URL to scrape"
    )
    image_dir: Path = Field(
        default_factory=get_default_tmp_dir,
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
        """
        Validator to ensure that 'image_dir' and 'output_file' fields are Path objects.
        
        Args:
            v (Union[str, Path]): The value to convert.
            
        Returns:
            Path: Converted Path object.
        """
        return Path(v) if not isinstance(v, Path) else v
    
    def __init__(self, **data):
        """
        Initializes the ScrapingConfig instance and ensures the image directory exists.
        """
        super().__init__(**data)
        
        # Create the image directory if it doesn't exist
        if not self.image_dir.exists():
            self.image_dir.mkdir(parents=True, exist_ok=True)
