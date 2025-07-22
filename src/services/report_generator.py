


import time
from typing import List, Dict
from pathlib import Path
from src.core.models import AnimalEntry, ScrapingConfig
from src.utils.logger import get_logger
from src.utils.decorators import timing_decorator

logger = get_logger(__name__)


class HTMLReportGenerator:
    """Generates HTML reports for the scraped data."""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
    
    @timing_decorator
    def generate_report(self, animal_entries: List[AnimalEntry], execution_time: float) -> Path:
        """
        Generate an HTML report of the scraped data.
        
        Args:
            animal_entries: List of AnimalEntry objects
            execution_time: Total execution time in seconds
            
        Returns:
            Path to the generated HTML file
        """
        html_content = self._build_html_content(animal_entries, execution_time)
        
        self.config.output_file.write_text(html_content, encoding='utf-8')
        logger.info(f"HTML report generated: {self.config.output_file}")
        
        return self.config.output_file
    
    def _build_html_content(self, animal_entries: List[AnimalEntry], execution_time: float) -> str:
        """Build the complete HTML content."""
        stats = self._calculate_statistics(animal_entries)
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Animal Names and Collateral Adjectives Report</title>
            <style>
                {self._get_css_styles()}
            </style>
        </head>
        <body>
            <header>
                <h1>Animal Names and Collateral Adjectives</h1>
                <p class="subtitle">Scraped from Wikipedia's List of Animal Names</p>
            </header>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>Total Entries</h3>
                    <p class="stat-number">{stats['total_entries']}</p>
                </div>
                <div class="stat-card">
                    <h3>Unique Animals</h3>
                    <p class="stat-number">{stats['unique_animals']}</p>
                </div>
                <div class="stat-card">
                    <h3>Unique Adjectives</h3>
                    <p class="stat-number">{stats['unique_adjectives']}</p>
                </div>
                <div class="stat-card">
                    <h3>Images Downloaded</h3>
                    <p class="stat-number">{stats['images_downloaded']}</p>
                </div>
                <div class="stat-card">
                    <h3>Execution Time</h3>
                    <p class="stat-number">{execution_time:.1f}s</p>
                </div>
            </div>
            
            <div class="content">
                <h2>Animal Entries ({len(animal_entries)} total)</h2>
                <div class="animal-grid">
                    {self._build_animal_cards(animal_entries)}
                </div>
            </div>
            
            <footer>
                <p>Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </footer>
        </body>
        </html>
        """
        return html
    
    def _calculate_statistics(self, animal_entries: List[AnimalEntry]) -> Dict[str, int]:
        """Calculate statistics for the report."""
        unique_animals = set(entry.animal_name for entry in animal_entries)
        unique_adjectives = set(entry.collateral_adjective for entry in animal_entries)
        images_downloaded = sum(1 for entry in animal_entries if entry.local_image_path)
        
        return {
            'total_entries': len(animal_entries),
            'unique_animals': len(unique_animals),
            'unique_adjectives': len(unique_adjectives),
            'images_downloaded': images_downloaded,
        }
    
    def _build_animal_cards(self, animal_entries: List[AnimalEntry]) -> str:
        """Build HTML cards for animal entries."""
        cards = []
        for entry in animal_entries:
            image_html = ""
            if entry.local_image_path and Path(entry.local_image_path).exists():
                image_html = f'<img src="file://{entry.local_image_path}" alt="{entry.animal_name}" class="animal-image">'
            
            card = f"""
            <div class="animal-card">
                {image_html}
                <div class="animal-info">
                    <h3 class="animal-name">{entry.animal_name}</h3>
                    <p class="adjective">Collateral adjective: <em>{entry.collateral_adjective}</em></p>
                </div>
            </div>
            """
            cards.append(card)
        
        return ''.join(cards)
    
    def _get_css_styles(self) -> str:
        """Return CSS styles for the HTML report."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 2rem 1rem;
            margin-bottom: 2rem;
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            max-width: 1200px;
            margin: 0 auto 2rem auto;
            padding: 0 1rem;
        }
        
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .stat-card h3 {
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.5rem;
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }
        
        .content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1rem;
        }
        
        .content h2 {
            margin-bottom: 1.5rem;
            color: #333;
        }
        
        .animal-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }
        
        .animal-card {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .animal-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .animal-image {
            width: 100%;
            height: 200px;
            object-fit: cover;
            border-bottom: 1px solid #eee;
        }
        
        .animal-info {
            padding: 1.5rem;
        }
        
        .animal-name {
            font-size: 1.3rem;
            margin-bottom: 0.5rem;
            color: #333;
        }
        
        .adjective {
            color: #666;
            font-size: 0.95rem;
        }
        
        .adjective em {
            color: #667eea;
            font-weight: 600;
        }
        
        footer {
            text-align: center;
            padding: 2rem;
            color: #666;
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            h1 {
                font-size: 2rem;
            }
            
            .stats {
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }
            
            .animal-grid {
                grid-template-columns: 1fr;
            }
        }
        """