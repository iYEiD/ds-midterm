"""
Integration script to scrape NBA stats and store in MongoDB
"""
import sys
import json
import subprocess
from pathlib import Path
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from scraper.storage import get_storage

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)


def scrape_and_store(url: str, output_file: str = "output.json") -> dict:
    """
    Scrape URL using Scrapy and store results in MongoDB
    
    Args:
        url: URL to scrape
        output_file: Temporary output file for scraped data
        
    Returns:
        Dictionary with scraping statistics
    """
    storage = get_storage()
    
    # Run the Scrapy spider
    logger.info(f"Starting scrape for URL: {url}")
    
    cmd = [
        sys.executable,
        str(project_root / "scraper" / "scrapy_runner.py"),
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Scraping failed: {result.stderr}")
        return {
            'status': 'failed',
            'error': result.stderr,
            'players_stored': 0
        }
    
    # Read the output file
    output_path = Path(output_file)
    if not output_path.exists():
        logger.error(f"Output file not found: {output_file}")
        return {
            'status': 'failed',
            'error': 'Output file not found',
            'players_stored': 0
        }
    
    # Load scraped data
    with open(output_path, 'r') as f:
        scraped_data = json.load(f)
    
    if not scraped_data:
        logger.error("No data scraped")
        return {
            'status': 'failed',
            'error': 'No data scraped',
            'players_stored': 0
        }
    
    # Process and store each result
    stats = {
        'status': 'success',
        'players_stored': 0,
        'tables_processed': 0
    }
    
    for result in scraped_data:
        url = result.get('url')
        headers = result.get('headers', [])
        data = result.get('data', [])
        table_index = result.get('table_index', 0)
        
        logger.info(f"Processing table {table_index} with {len(data)} players")
        
        # Store raw HTML/JSON
        storage.store_raw_html(
            url=url,
            html_content=json.dumps(result, indent=2),
            status='success',
            metadata={
                'row_count': len(data),
                'headers': headers,
                'table_index': table_index,
                'scraper': 'scrapy-playwright'
            }
        )
        
        # Store processed stats for each player
        for player_data in data:
            player_name = player_data.get('PLAYER', 'Unknown')
            
            if player_name and player_name != 'Unknown':
                # Determine stat category from URL
                if 'StatCategory=STL' in url:
                    stat_category = 'steals'
                elif 'StatCategory=PTS' in url:
                    stat_category = 'points'
                elif 'StatCategory=AST' in url:
                    stat_category = 'assists'
                elif 'StatCategory=REB' in url:
                    stat_category = 'rebounds'
                else:
                    stat_category = 'unknown'
                
                # Add extra metadata to stats
                enriched_stats = player_data.copy()
                enriched_stats['stat_category'] = stat_category
                enriched_stats['source_url'] = url
                
                storage.store_processed_stats(
                    player_name=player_name,
                    stats=enriched_stats,
                    season_type="Regular Season"
                )
                stats['players_stored'] += 1
        
        stats['tables_processed'] += 1
    
    logger.info(f"Stored {stats['players_stored']} players from {stats['tables_processed']} tables")
    
    # Clean up output file
    output_path.unlink(missing_ok=True)
    
    return stats


def main():
    """Main function for testing"""
    # Test URLs for different stat categories
    test_urls = [
        "https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=STL",
        # Add more URLs as needed
    ]
    
    for url in test_urls:
        print(f"\n{'='*80}")
        print(f"Scraping: {url}")
        print('='*80)
        
        stats = scrape_and_store(url)
        
        print(f"\nResults:")
        print(f"  Status: {stats['status']}")
        print(f"  Players stored: {stats['players_stored']}")
        print(f"  Tables processed: {stats.get('tables_processed', 0)}")
        
        if stats['status'] == 'failed':
            print(f"  Error: {stats.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
