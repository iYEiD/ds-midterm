"""
Kafka-based Scraper Worker
Consumes URLs from Kafka, scrapes them, and produces results back to Kafka
"""
import sys
import json
import signal
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from scraper.url_manager import get_url_manager
from scraper.storage import get_storage
from scraper.scrapy_runner import run_spider

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)


class ScraperWorker:
    """Worker that consumes scraping tasks from Kafka"""
    
    def __init__(self, worker_id: str = "worker-1"):
        """
        Initialize scraper worker
        
        Args:
            worker_id: Unique identifier for this worker
        """
        self.worker_id = worker_id
        self.url_manager = get_url_manager()
        self.storage = get_storage()
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"ScraperWorker {worker_id} initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def scrape_url(self, url: str, metadata: Dict) -> Dict:
        """
        Scrape a single URL using Scrapy
        
        Args:
            url: URL to scrape
            metadata: Task metadata
            
        Returns:
            Result dictionary
        """
        logger.info(f"[{self.worker_id}] Scraping: {url}")
        
        try:
            # Check if URL already scraped
            if self.storage.url_exists(url):
                logger.warning(f"URL already scraped: {url}")
                return {
                    'status': 'skipped',
                    'url': url,
                    'reason': 'already_scraped',
                    'worker_id': self.worker_id
                }
            
            # Run Scrapy spider using subprocess
            import subprocess
            
            cmd = [
                sys.executable,
                str(project_root / "scraper" / "scrapy_runner.py"),
                url
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Scraping failed: {result.stderr}")
                return {
                    'status': 'failed',
                    'url': url,
                    'error': result.stderr[:500],
                    'worker_id': self.worker_id
                }
            
            # Read the scraped data from output.json
            output_file = Path("output.json")
            if not output_file.exists():
                logger.error("Output file not found")
                return {
                    'status': 'failed',
                    'url': url,
                    'error': 'Output file not found',
                    'worker_id': self.worker_id
                }
            
            # Load and store scraped data
            with open(output_file, 'r') as f:
                scraped_data = json.load(f)
            
            if not scraped_data:
                logger.error("No data scraped")
                return {
                    'status': 'failed',
                    'url': url,
                    'error': 'No data scraped',
                    'worker_id': self.worker_id
                }
            
            # Store in MongoDB
            for item in scraped_data:
                item_url = item.get('url')
                data = item.get('data', [])
                headers = item.get('headers', [])
                
                self.storage.store_raw_html(
                    url=item_url,
                    html_content=json.dumps(item, indent=2),
                    status='success',
                    metadata={
                        'row_count': len(data),
                        'headers': headers,
                        'worker_id': self.worker_id,
                        'scraper': 'scrapy-playwright',
                        **metadata
                    }
                )
                
                logger.info(f"Stored {len(data)} rows for {item_url}")
            
            # Clean up output file
            output_file.unlink(missing_ok=True)
            
            return {
                'status': 'success',
                'url': url,
                'rows_scraped': sum(len(item.get('data', [])) for item in scraped_data),
                'worker_id': self.worker_id
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Scraping timeout for {url}")
            return {
                'status': 'failed',
                'url': url,
                'error': 'Timeout',
                'worker_id': self.worker_id
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                'status': 'failed',
                'url': url,
                'error': str(e),
                'worker_id': self.worker_id
            }
    
    def process_message(self, message: Dict) -> Dict:
        """
        Process a Kafka message
        
        Args:
            message: Message from Kafka
            
        Returns:
            Processing result
        """
        url = message.get('url')
        metadata = message.get('metadata', {})
        priority = message.get('priority', 0)
        
        if not url:
            logger.error("Message missing URL")
            return {'status': 'invalid', 'error': 'Missing URL'}
        
        # Scrape the URL
        result = self.scrape_url(url, metadata)
        
        # Add metadata
        result['priority'] = priority
        result['metadata'] = metadata
        
        return result
    
    def run(self):
        """
        Main worker loop - consume messages from Kafka
        """
        logger.info(f"[{self.worker_id}] Starting worker loop...")
        
        # Create consumer
        consumer = self.url_manager.create_consumer(
            group_id="scraper-workers",
            auto_offset_reset='earliest'
        )
        
        if not consumer:
            logger.error("Failed to create Kafka consumer")
            return
        
        logger.info(f"[{self.worker_id}] Listening for tasks on topic: {settings.KAFKA_SCRAPING_TASKS_TOPIC}")
        
        try:
            for message in consumer:
                if not self.running:
                    logger.info("Worker shutting down...")
                    break
                
                try:
                    # Parse message
                    task = message.value
                    logger.info(f"[{self.worker_id}] Received task: {task.get('url', 'Unknown')}")
                    
                    # Process the task
                    result = self.process_message(task)
                    
                    # Submit result back to Kafka
                    self.url_manager.submit_result(result)
                    
                    logger.info(f"[{self.worker_id}] Task completed: {result['status']}")
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Continue to next message
                    
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            consumer.close()
            logger.info(f"[{self.worker_id}] Worker stopped")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Kafka Scraper Worker')
    parser.add_argument('--worker-id', type=str, default='worker-1', 
                       help='Unique worker ID')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"KAFKA SCRAPER WORKER - {args.worker_id}")
    print('='*60)
    
    worker = ScraperWorker(worker_id=args.worker_id)
    worker.run()


if __name__ == "__main__":
    main()
