"""
Scrapy spider for NBA all-time leaders statistics
Uses Playwright to handle JavaScript-rendered content
"""
import scrapy
from scrapy_playwright.page import PageMethod
import json
from typing import Dict, Any
from datetime import datetime


class NBALeadersSpider(scrapy.Spider):
    """Spider for scraping NBA all-time leaders stats"""
    
    name = "nba_leaders"
    allowed_domains = ["nba.com"]
    
    # Default start URL - can be overridden
    start_urls = [
        "https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=STL"
    ]
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
        },
        'CONCURRENT_REQUESTS': 1,  # NBA.com is sensitive to concurrent requests
        'DOWNLOAD_DELAY': 2,
    }
    
    def start_requests(self):
        """Generate initial requests with Playwright"""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "table", timeout=30000),
                        PageMethod("wait_for_timeout", 3000),  # Wait for data to load
                    ],
                },
                callback=self.parse,
                errback=self.errback
            )
    
    async def parse(self, response):
        """Parse the NBA stats page"""
        self.logger.info(f"Parsing page: {response.url}")
        
        # Close the playwright page
        page = response.meta.get("playwright_page")
        if page:
            await page.close()
        
        # Extract the table data
        tables = response.css('table')
        
        if not tables:
            self.logger.warning("No tables found on page")
            yield {
                'url': response.url,
                'status': 'no_tables',
                'html_length': len(response.text)
            }
            return
        
        # Parse each table
        for table_idx, table in enumerate(tables):
            # Get headers
            headers = []
            
            # Try multiple header selectors
            header_rows = table.css('thead tr')
            if header_rows:
                # Get the last header row (in case there are multiple)
                header_row = header_rows[-1]
                headers = header_row.css('th::text, th a::text').getall()
                headers = [h.strip() for h in headers if h.strip()]
            
            if not headers:
                self.logger.warning(f"No headers found in table {table_idx}")
                continue
            
            self.logger.info(f"Found headers: {headers}")
            
            # Get data rows
            rows = table.css('tbody tr')
            
            player_data = []
            for row in rows:
                cells = row.css('td')
                
                if len(cells) == 0:
                    continue
                
                # Extract text from each cell
                row_data = {}
                for idx, cell in enumerate(cells):
                    if idx < len(headers):
                        # Try to get text, handle links
                        cell_text = cell.css('::text').get()
                        if not cell_text:
                            cell_text = cell.css('a::text').get()
                        if not cell_text:
                            cell_text = ""
                        
                        row_data[headers[idx]] = cell_text.strip()
                
                if row_data:
                    player_data.append(row_data)
            
            self.logger.info(f"Extracted {len(player_data)} players from table {table_idx}")
            
            # Yield the scraped data
            yield {
                'url': response.url,
                'table_index': table_idx,
                'headers': headers,
                'data': player_data,
                'row_count': len(player_data),
                'scraped_at': datetime.utcnow().isoformat(),
                'status': 'success'
            }
    
    async def errback(self, failure):
        """Handle request failures"""
        self.logger.error(f"Request failed: {failure.request.url}")
        self.logger.error(f"Error: {failure.value}")
        
        # Close playwright page if it exists
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
