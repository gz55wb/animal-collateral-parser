from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Tuple
import re
import logging
from src.utils.decorators import timing_decorator
from src.utils.config_loader import load_config
from src.utils.config_loader import clean_text_with_config


logger = logging.getLogger(__name__)
config = load_config()
COLLATERAL_KEYWORDS = config["collateral_keywords"]
TRIVIAL_NAME_KEYWORDS = config["trivial_name_keywords"]

class AnimalDataParser:
    """
    Parser class to extract animal names, collateral adjectives, and relevant links from
    the Wikipedia page HTML content of animal names.
    """

    @timing_decorator
    def parse_wikipedia_page(self, html_content: str) -> List[Tuple[str, str, List[str]]]:
        """
        Parses the provided Wikipedia HTML content to extract tuples of:
        (animal_name, collateral_adjective, list_of_links).

        Args:
            html_content (str): Raw HTML content of the Wikipedia page.

        Returns:
            List[Tuple[str, str, List[str]]]: List of tuples, each containing:
                - animal_name (str)
                - collateral_adjective (str)
                - links (List[str]): List of Wikipedia URLs related to the animal.
        """
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
            trivial_name_idx = 1  # Animal name usually in column 1

            for idx, cell in enumerate(header_cells):
                header_text = cell.get_text(strip=True).lower()
                if any(keyword in header_text for keyword in COLLATERAL_KEYWORDS):
                    collateral_idx = idx
                if any(keyword in header_text for keyword in TRIVIAL_NAME_KEYWORDS):
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
        """
        Cleans and extracts text content from a table cell, using configured regex-based cleanup.

        Args:
            cell (Tag): BeautifulSoup Tag object representing a table cell.

        Returns:
            str: Cleaned text content from the cell.
        """
        text = cell.get_text(separator=' ', strip=True)
        return clean_text_with_config(text)


    def _extract_links_from_cell(self, cell: Tag) -> List[str]:
        """
        Extracts full Wikipedia URLs from anchor tags within a table cell.

        Args:
            cell (Tag): BeautifulSoup Tag object representing a table cell.

        Returns:
            List[str]: List of full Wikipedia URLs found in the cell.
        """
        links = []
        for a_tag in cell.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('/wiki/'):
                links.append('https://en.wikipedia.org' + href)
        return links
