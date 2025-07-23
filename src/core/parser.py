from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Tuple
import re
import logging
from src.utils.decorators import timing_decorator

logger = logging.getLogger(__name__)

class AnimalDataParser:

    
    @timing_decorator
    def parse_wikipedia_page(self, html_content: str) -> List[Tuple[str, str, List[str]]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        animal_data = []

        tables = soup.find_all('table', class_='wikitable')
        logger.info(f"Found {len(tables)} tables")

        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            if not rows:
                continue

            header_cells = rows[0].find_all(['th', 'td'])
            collateral_idx = -1
            trivial_name_idx = 1  # שם החיה לרוב בעמודה 1

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

                links = self._extract_links_from_cell(cells[trivial_name_idx])

                collateral_cell = cells[collateral_idx]
                adjectives = [
                    adj.strip()
                    for adj in re.split(r"[,\s]+", self._extract_text_from_cell(collateral_cell))
                    if adj.strip()
                ]

                for adj in adjectives:
                    animal_data.append((animal_name, adj, links))

        logger.info(f"Extracted {len(animal_data)} animal-adjective-link triples")
        return animal_data


    def _extract_text_from_cell(self, cell: Tag) -> str:
        text = cell.get_text(separator=' ', strip=True)
        text = re.sub(r'\[[^\]]*\]', '', text)  # remove [1], [a], etc.
        text = re.sub(r'\([^)]*\)', '', text)    # remove ( )
        text = re.sub(r'\b(also )?see\b.*', '', text, flags=re.IGNORECASE)
        text = text.split('/')[0]
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_links_from_cell(self, cell: Tag) -> List[str]:
        links = []
        for a_tag in cell.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('/wiki/'):
                links.append('https://en.wikipedia.org' + href)
        return links
