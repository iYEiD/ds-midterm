"""
Scrapy settings for NBA stats scraper
"""
from config import settings

BOT_NAME = 'nba_scraper'

SPIDER_MODULES = ['scraper']
NEWSPIDER_MODULE = 'scraper'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure download handlers for Playwright
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Use asyncio reactor
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Playwright settings
PLAYWRIGHT_BROWSER_TYPE = 'chromium'
PLAYWRIGHT_LAUNCH_OPTIONS = {
    'headless': True,
    'timeout': 60000,  # 60 seconds
}

# Configure maximum concurrent requests performed by Scrapy
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = settings.SCRAPER_DELAY

# Disable cookies
COOKIES_ENABLED = False

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
    'User-Agent': settings.SCRAPER_USER_AGENT,
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware': 50,
}

# Configure item pipelines
ITEM_PIPELINES = {
    'scraper.scrapy_nba_scraper.ItemStoragePipeline': 300,
}

# Set log level
LOG_LEVEL = 'INFO'
