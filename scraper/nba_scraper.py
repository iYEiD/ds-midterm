"""
NBA Stats Scraper
Simple scraper for NBA statistics pages
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
from loguru import logger
import sys
import time
from datetime import datetime

from config import settings
from scraper.storage import get_storage
from scraper.url_manager import get_url_manager

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)


class NBAStatsScraper:
    """Scraper for NBA stats pages"""
    
    def __init__(self):
        """Initialize scraper"""
        self.user_agent = settings.SCRAPER_USER_AGENT
        self.delay = settings.SCRAPER_DELAY
        self.timeout = settings.SCRAPER_TIMEOUT
        self.max_retries = settings.SCRAPER_MAX_RETRIES
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.storage = get_storage()
        logger.info("NBA Stats Scraper initialized")
    
    def scrape_url(self, url: str, save_to_db: bool = True) -> Optional[Dict]:
        """
        Scrape a single URL
        
        Args:
            url: URL to scrape
            save_to_db: Whether to save raw HTML to database
            
        Returns:
            Dictionary with scraping results or None if failed
        """
        # Check if already scraped
        if save_to_db and self.storage.url_exists(url):
            logger.info(f"URL already in database: {url}")
            existing = self.storage.get_raw_html(url)
            return {
                "url": url,
                "status": "exists",
                "html": existing.get("html_content") if existing else None,
                "from_cache": True
            }
        
        # Try scraping with retries
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Scraping URL (attempt {attempt + 1}/{self.max_retries}): {url}")
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                html_content = response.text
                
                # Save to database if requested
                if save_to_db:
                    self.storage.store_raw_html(
                        url=url,
                        html_content=html_content,
                        status="success",
                        metadata={
                            "status_code": response.status_code,
                            "content_length": len(html_content),
                            "scraped_at": datetime.utcnow().isoformat()
                        }
                    )
                    self.storage.update_scraping_metadata(url, status="scraped")
                
                logger.success(f"Successfully scraped: {url}")
                
                # Respect rate limiting
                time.sleep(self.delay)
                
                return {
                    "url": url,
                    "status": "success",
                    "html": html_content,
                    "status_code": response.status_code,
                    "from_cache": False
                }
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * self.delay
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All attempts failed for {url}")
                    
                    if save_to_db:
                        self.storage.store_raw_html(
                            url=url,
                            html_content="",
                            status="failed",
                            metadata={"error": str(e)}
                        )
                        self.storage.update_scraping_metadata(url, status="failed")
                    
                    return {
                        "url": url,
                        "status": "failed",
                        "error": str(e),
                        "from_cache": False
                    }
        
        return None
    
    def parse_nba_table(self, html: str) -> List[Dict]:
        """
        Parse NBA stats table from HTML
        
        Args:
            html: HTML content
            
        Returns:
            List of player statistics dictionaries
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Find all tables (NBA.com uses various table structures)
            tables = soup.find_all('table')
            
            if not tables:
                logger.warning("No tables found in HTML")
                return []
            
            results = []
            
            for table in tables:
                # Find headers
                headers = []
                header_row = table.find('thead')
                if header_row:
                    headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
                
                # Find data rows
                tbody = table.find('tbody')
                if not tbody:
                    continue
                
                rows = tbody.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) == len(headers):
                        row_data = {}
                        for header, cell in zip(headers, cells):
                            row_data[header] = cell.get_text(strip=True)
                        results.append(row_data)
            
            logger.info(f"Parsed {len(results)} rows from HTML")
            return results
            
        except Exception as e:
            logger.error(f"Error parsing NBA table: {e}")
            return []
    
    def scrape_and_parse(self, url: str) -> Optional[Dict]:
        """
        Scrape URL and parse the content
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with parsed data
        """
        result = self.scrape_url(url)
        
        if not result or result["status"] not in ["success", "exists"]:
            return result
        
        # Parse the HTML
        parsed_data = self.parse_nba_table(result["html"])
        result["parsed_data"] = parsed_data
        result["row_count"] = len(parsed_data)
        
        return result
    
    def close(self):
        """Close scraper resources"""
        self.session.close()
        logger.info("Scraper closed")


def scrape_nba_leaders_page():
    """
    Example function to scrape NBA all-time leaders page
    """
    scraper = NBAStatsScraper()
    
    # NBA all-time leaders URL
    url = "https://www.nba.com/stats/alltime-leaders"
    
    try:
        result = scraper.scrape_and_parse(url)
        
        if result and result["status"] in ["success", "exists"]:
            logger.success(f"Scraped and parsed {result.get('row_count', 0)} rows")
            return result
        else:
            logger.error("Failed to scrape NBA leaders page")
            return None
            
    finally:
        scraper.close()


if __name__ == "__main__":
    # Test the scraper
    result = scrape_nba_leaders_page()
    if result:
        print(f"\nSuccessfully scraped {result.get('row_count', 0)} player stats")
        print(f"From cache: {result.get('from_cache', False)}")
        
        # Print first few rows as sample
        if result.get("parsed_data"):
            print("\nSample data (first 5 rows):")
            for i, row in enumerate(result["parsed_data"][:5], 1):
                print(f"{i}. {row}")
