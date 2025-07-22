from ast import Dict
from bs4 import BeautifulSoup, Tag
import re
import logging
from typing import List, Dict
from src.utils.logger import get_logger
from src.utils.decorators import timing_decorator


logger = get_logger(__name__)

class AnimalDataParser:
    """Parses Wikipedia page to extract animal names and collateral adjectives."""
    
    @timing_decorator
    def parse_wikipedia_page(self, html_content: str) -> Dict[str, List[str]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        animal_adjective_pairs = {}

        tables = soup.find_all('table', class_='wikitable')
        logger.info(f"Found {len(tables)} tables")

        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            if not rows:
                continue

            # מציאת אינדקס העמודה של "Collateral adjective"
            header_cells = rows[0].find_all(['th', 'td'])
            collateral_idx = -1
            trivial_name_idx = 1  # בדרך כלל שם החיה נמצא בעמודה 1 (יכול להשתנות)

            for idx, cell in enumerate(header_cells):
                header_text = cell.get_text(strip=True).lower()
                if 'collateral adjective' in header_text:
                    collateral_idx = idx
                if 'scientific term' in header_text or 'animal' in header_text:
                    trivial_name_idx = idx

            if collateral_idx == -1:
                logger.warning(f"Table {i}: No 'Collateral adjective' column found.")
                continue

            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) <= max(collateral_idx, trivial_name_idx):
                    continue

                animal_name = self._extract_text_from_cell(cells[trivial_name_idx])
                if not animal_name:
                    continue

                collateral_cell = cells[collateral_idx]
                collateral_text = self._extract_text_from_cell(collateral_cell)

                # לפצל במידה ויש כמה תארים נלווים מופרדים בפסיקים
                adjectives = [adj.strip() for adj in collateral_text.split(',') if adj.strip()]
                
                if animal_name not in animal_adjective_pairs:
                    animal_adjective_pairs[animal_name] = adjectives

        logger.info(f"Extracted {len(animal_adjective_pairs)} animal-adjective pairs")
        return  animal_adjective_pairs


    
    def _extract_text_from_cell(self, cell: Tag) -> str:
        """Extract clean primary animal name from a table cell."""
        text = cell.get_text(separator=' ', strip=True)

        # Remove citation markers like [1], [ 80 ], etc.
        text = re.sub(r'\[\s*\d+\s*\]', '', text)

        # Remove content in parentheses
        text = re.sub(r'\([^)]*\)', '', text)

        # Remove 'Also see ...' or 'see ...'
        text = re.sub(r'\b(also )?see\b.*', '', text, flags=re.IGNORECASE)

        # Remove everything after slash (if exists)
        text = text.split('/')[0]

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()



    
    # def _is_likely_adjective(self, text: str) -> bool:
    #     """Check if text is likely a collateral adjective."""
    #     if not text or len(text) < 2:
    #         return False
        
    #     # Filter out common non-adjective patterns
    #     exclude_patterns = [
    #         r'^\d+$',  # Just numbers
    #         r'^[A-Z]{2,}$',  # All caps abbreviations
    #         r'species$',  # Ends with 'species'
    #         r'animal$',  # Ends with 'animal'
    #     ]
        
    #     for pattern in exclude_patterns:
    #         if re.match(pattern, text, re.IGNORECASE):
    #             return False
        
    #     return True