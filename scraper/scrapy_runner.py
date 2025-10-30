"""
Simple runner for Scrapy spider that can be called multiple times
"""
import sys
from pathlib import Path
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from scraper.scrapy_spider import NBALeadersSpider


def run_spider(url: str):
    """Run spider with given URL"""
    # Configure Scrapy settings
    process = CrawlerProcess({
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
        'FEEDS': {
            'output.json': {
                'format': 'json',
                'overwrite': True,
            },
        },
    })
    
    # Set start URL
    NBALeadersSpider.start_urls = [url]
    
    # Run the spider
    process.crawl(NBALeadersSpider)
    process.start()


if __name__ == "__main__":
    # Get URL from command line or use default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=STL"
    
    print(f"Running spider for URL: {url}")
    run_spider(url)
