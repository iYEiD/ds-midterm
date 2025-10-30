"""
Scrapy-based NBA scraper using Playwright for JavaScript rendering
This integrates Scrapy spider with our storage and URL management system
"""
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from twisted.internet import reactor, defer
from typing import List, Dict, Optional
from loguru import logger
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from scraper.storage import get_storage
from scraper.scrapy_spider import NBALeadersSpider

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)

# Store global results
_scraped_items = []


class ScrapyNBAScraper:
    """Wrapper for Scrapy spider with our storage system"""
    
    def __init__(self):
        """Initialize scraper"""
        self.storage = get_storage()
        self.results = []
        logger.info("Scrapy NBA Scraper initialized")
    
    def scrape_urls(self, urls: List[str], save_to_db: bool = True) -> List[Dict]:
        """
        Scrape URLs using Scrapy with Playwright
        
        Args:
            urls: List of URLs to scrape
            save_to_db: Whether to save to database
            
        Returns:
            List of scraping results
        """
        global _scraped_items
        _scraped_items = []
        storage = self.storage
        
        # Create custom spider class with storage
        class CustomNBASpider(NBALeadersSpider):
            start_urls = urls
            
            def parse(self, response):
                # Call parent parse method
                for item in super().parse(response):
                    item_dict = dict(item)
                    _scraped_items.append(item_dict)
                    
                    if save_to_db:
                        # Save raw HTML and parsed data to MongoDB
                        url = item_dict.get('url')
                        data = item_dict.get('data', [])
                        
                        # Store in MongoDB
                        if url and data:
                            storage.store_raw_html(
                                url=url,
                                html_content=json.dumps(item_dict),
                                status=item_dict.get('status', 'success'),
                                metadata={
                                    'row_count': item_dict.get('row_count', 0),
                                    'headers': item_dict.get('headers', []),
                                    'table_index': item_dict.get('table_index', 0)
                                }
                            )
                            
                            # Store processed stats for each player
                            for player_data in data:
                                player_name = player_data.get('PLAYER', 'Unknown')
                                if player_name and player_name != 'Unknown':
                                    storage.store_processed_stats(
                                        player_name=player_name,
                                        stats=player_data,
                                        season_type="Regular Season"
                                    )
                            
                            logger.info(f"Stored {len(data)} player stats in MongoDB")
                    
                    yield item
        
        # Configure Scrapy
        configure_logging({'LOG_LEVEL': 'INFO'})
        runner = CrawlerRunner({
            'USER_AGENT': settings.SCRAPER_USER_AGENT,
            'ROBOTSTXT_OBEY': False,
            'CONCURRENT_REQUESTS': 1,
            'DOWNLOAD_DELAY': settings.SCRAPER_DELAY,
            'LOG_LEVEL': 'INFO',
            'DOWNLOAD_HANDLERS': {
                "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
                "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            },
            'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
            'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
            'PLAYWRIGHT_LAUNCH_OPTIONS': {
                'headless': True,
            },
        })
        
        # Run the spider
        @defer.inlineCallbacks
        def crawl():
            yield runner.crawl(CustomNBASpider)
            reactor.stop()
        
        try:
            crawl()
            reactor.run()  # This blocks until crawling is finished
            
            logger.info(f"Scrapy crawling completed. Results: {len(_scraped_items)}")
            self.results = _scraped_items
            
            return _scraped_items
            
        except Exception as e:
            logger.error(f"Error during Scrapy crawling: {e}")
            return []
    
    def scrape_url(self, url: str, save_to_db: bool = True) -> Optional[Dict]:
        """
        Scrape a single URL
        
        Args:
            url: URL to scrape
            save_to_db: Whether to save to database
            
        Returns:
            Scraping result or None
        """
        results = self.scrape_urls([url], save_to_db)
        return results[0] if results else None


class ItemStoragePipeline:
    """Scrapy pipeline for storing items"""
    
    def process_item(self, item, spider):
        """Process and store scraped item"""
        return item


def test_scrapy_scraper():
    """Test the Scrapy scraper"""
    # Target URL with steals leaders
    test_url = "https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=STL"
    
    logger.info(f"Testing Scrapy scraper with URL: {test_url}")
    
    scraper = ScrapyNBAScraper()
    result = scraper.scrape_url(test_url, save_to_db=True)
    
    if result:
        print("\n" + "="*60)
        print("SCRAPY SCRAPING RESULT")
        print("="*60)
        print(f"URL: {result.get('url')}")
        print(f"Status: {result.get('status')}")
        print(f"Row Count: {result.get('row_count')}")
        print(f"Headers: {result.get('headers')}")
        
        # Print first 5 players
        data = result.get('data', [])
        if data:
            print(f"\nFirst 5 players:")
            for i, player in enumerate(data[:5], 1):
                print(f"{i}. {player}")
        
        print("\n" + "="*60)
    else:
        print("❌ Scraping failed")


if __name__ == "__main__":
    test_scrapy_scraper()
