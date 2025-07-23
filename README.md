# AnimalScraper

AnimalScraper is a Python-based web scraping tool designed to extract animal names and their collateral adjectives from Wikipedia. It also downloads relevant animal images and generates a comprehensive HTML report summarizing the collected data.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Notes](#notes)
- [License](#license)

## Features

- Parses Wikipedia's "List of animal names" page to extract animal names and collateral adjectives
- Handles multiple adjectives per animal entry
- Downloads animal images asynchronously with concurrency control
- Generates an easy-to-navigate HTML report with embedded local image links
- Modular design allowing easy extension and configuration

## Installation

1. **Clone the repository**
   ```bash
   git clone https://your-repo-url.git
   cd AnimalScraper
   ```

2. **Create and activate a Python virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the main scraper and generate the HTML report, execute:

```bash
python -m src.initialization.main
```

The script will:
- Fetch and parse the Wikipedia page
- Extract animal and collateral adjective data
- Download images concurrently
- Generate an HTML report saved to the configured output path

## Running Tests

Automated tests are provided to validate parsing logic, data models, and async operations.

Run the test suite using:

```bash
python -m pytest tests/animal_scraper_tests.py
```

## Project Structure

```
AnimalScraper/
├── src/
│   ├── core/              # Core scraping logic and data models
│   ├── services/          # Image downloading, finding, and report generation
│   ├── utils/             # Utilities like config loader and decorators
│   └── initialization/    # Entry point for running the scraper
├── tests/                 # Test cases and fixtures
├── requirements.txt       # Project dependencies
└── README.md              # This documentation file
```

## Configuration

Default configuration values such as:
- Wikipedia URL to scrape
- Image download directory
- Output report filename
- Concurrency limits
- Request timeouts

can be customized via configuration files or environment variables loaded by the config_loader utility in `src/utils/`.

## Notes

- The project uses asynchronous programming (asyncio + aiohttp) to efficiently download images
- Images are saved locally, and report links point to these local files
- Ensure your Python environment is active before running commands
- Python 3.8+ is recommended
