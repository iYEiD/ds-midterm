"""
Job Orchestrator for Distributed Scraping
Submits URLs to Kafka and monitors progress
"""
import sys
import time
from pathlib import Path
from typing import List, Dict
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from scraper.url_manager import get_url_manager
from scraper.storage import get_storage

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)


class JobOrchestrator:
    """Orchestrates distributed scraping jobs"""
    
    def __init__(self):
        """Initialize orchestrator"""
        self.url_manager = get_url_manager()
        self.storage = get_storage()
        logger.info("JobOrchestrator initialized")
    
    def submit_scraping_job(self, urls: List[str], metadata: Dict = None) -> Dict:
        """
        Submit a batch of URLs for scraping
        
        Args:
            urls: List of URLs to scrape
            metadata: Optional metadata for the job
            
        Returns:
            Job submission result
        """
        logger.info(f"Submitting scraping job with {len(urls)} URLs")
        
        # Filter out already scraped URLs
        new_urls = []
        skipped = 0
        
        for url in urls:
            if self.storage.url_exists(url):
                logger.debug(f"Skipping already scraped: {url}")
                skipped += 1
            else:
                new_urls.append(url)
        
        if not new_urls:
            logger.warning("All URLs already scraped")
            return {
                'status': 'no_new_urls',
                'total_urls': len(urls),
                'skipped': skipped,
                'submitted': 0
            }
        
        # Submit URLs to Kafka
        submitted = self.url_manager.submit_urls_batch(new_urls, metadata=metadata)
        
        logger.info(f"Submitted {submitted} URLs to Kafka (skipped {skipped})")
        
        return {
            'status': 'success',
            'total_urls': len(urls),
            'skipped': skipped,
            'submitted': submitted,
            'new_urls': new_urls
        }
    
    def monitor_job_progress(self, timeout: int = 300, poll_interval: int = 5) -> Dict:
        """
        Monitor job progress
        
        Args:
            timeout: Maximum time to wait (seconds)
            poll_interval: Time between checks (seconds)
            
        Returns:
            Progress statistics
        """
        logger.info(f"Monitoring job progress (timeout: {timeout}s)...")
        
        start_time = time.time()
        last_count = 0
        
        while time.time() - start_time < timeout:
            # Get pending count
            pending = self.url_manager.get_pending_count()
            
            # Get stats from MongoDB
            stats = self.storage.get_stats_count()
            
            elapsed = int(time.time() - start_time)
            
            logger.info(f"[{elapsed}s] Pending: {pending} | Processed: {stats['processed_stats_count']}")
            
            # Check if work is done
            if pending == 0 and stats['processed_stats_count'] > last_count:
                logger.info("Job appears complete!")
                break
            
            last_count = stats['processed_stats_count']
            time.sleep(poll_interval)
        
        # Final stats
        final_stats = self.storage.get_stats_count()
        
        return {
            'status': 'completed' if pending == 0 else 'timeout',
            'elapsed_time': int(time.time() - start_time),
            'stats': final_stats
        }
    
    def run_scraping_job(self, urls: List[str], metadata: Dict = None, 
                        monitor: bool = True, timeout: int = 300) -> Dict:
        """
        Submit and optionally monitor a scraping job
        
        Args:
            urls: List of URLs to scrape
            metadata: Optional metadata
            monitor: Whether to monitor progress
            timeout: Monitoring timeout
            
        Returns:
            Job result
        """
        # Submit job
        submission_result = self.submit_scraping_job(urls, metadata)
        
        if submission_result['status'] != 'success':
            return submission_result
        
        # Monitor if requested
        if monitor and submission_result['submitted'] > 0:
            progress = self.monitor_job_progress(timeout=timeout)
            return {
                **submission_result,
                'progress': progress
            }
        
        return submission_result


def test_orchestrator():
    """Test the orchestrator with sample URLs"""
    print(f"\n{'='*60}")
    print("JOB ORCHESTRATOR TEST")
    print('='*60)
    
    orchestrator = JobOrchestrator()
    
    # NBA stat URLs for different categories
    test_urls = [
        "https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=PTS",
        "https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=REB",
        "https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=AST",
    ]
    
    print(f"\nSubmitting {len(test_urls)} URLs for scraping...")
    print("URLs:")
    for i, url in enumerate(test_urls, 1):
        category = url.split('StatCategory=')[-1]
        print(f"  {i}. {category} leaders")
    
    # Submit job
    result = orchestrator.run_scraping_job(
        urls=test_urls,
        metadata={'job_type': 'test', 'categories': ['PTS', 'REB', 'AST']},
        monitor=True,
        timeout=180  # 3 minutes
    )
    
    print(f"\nJob Result:")
    print(f"  Status: {result['status']}")
    print(f"  Total URLs: {result['total_urls']}")
    print(f"  Submitted: {result['submitted']}")
    print(f"  Skipped: {result['skipped']}")
    
    if 'progress' in result:
        progress = result['progress']
        print(f"\nProgress:")
        print(f"  Status: {progress['status']}")
        print(f"  Elapsed: {progress['elapsed_time']}s")
        print(f"  Stats: {progress['stats']}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Job Orchestrator')
    parser.add_argument('--urls', nargs='+', help='URLs to scrape')
    parser.add_argument('--url-file', type=str, help='File containing URLs (one per line)')
    parser.add_argument('--monitor', action='store_true', help='Monitor job progress')
    parser.add_argument('--timeout', type=int, default=300, help='Monitoring timeout (seconds)')
    parser.add_argument('--test', action='store_true', help='Run test with sample URLs')
    
    args = parser.parse_args()
    
    if args.test:
        test_orchestrator()
        return
    
    # Get URLs from arguments or file
    urls = []
    
    if args.urls:
        urls = args.urls
    elif args.url_file:
        with open(args.url_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    else:
        print("Error: Provide --urls or --url-file")
        parser.print_help()
        return
    
    # Run orchestrator
    orchestrator = JobOrchestrator()
    result = orchestrator.run_scraping_job(
        urls=urls,
        monitor=args.monitor,
        timeout=args.timeout
    )
    
    print(f"\nResult: {result}")


if __name__ == "__main__":
    main()
