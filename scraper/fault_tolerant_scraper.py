"""
Fault-tolerant scraper with retry logic and dead letter queue.
Handles failures gracefully with exponential backoff.
"""
import time
import json
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scraper.url_manager import get_url_manager
from scraper.storage import get_storage

class RetryConfig:
    """Configuration for retry logic"""
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 5  # seconds
    MAX_BACKOFF = 300  # 5 minutes
    BACKOFF_MULTIPLIER = 2
    
class FaultTolerantScraper:
    """
    Scraper worker with fault tolerance features:
    - Exponential backoff retry
    - Dead letter queue for permanent failures
    - Error tracking and reporting
    - Graceful degradation
    """
    
    def __init__(self, worker_id: str = "ft-scraper-1"):
        """Initialize fault-tolerant scraper"""
        self.worker_id = worker_id
        self.url_manager = get_url_manager()
        self.storage = get_storage()
        self.retry_config = RetryConfig()
        
        # Statistics
        self.stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "retried": 0,
            "dead_lettered": 0
        }
        
        logger.info(f"FaultTolerantScraper '{worker_id}' initialized")
    
    def exponential_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay
        
        Args:
            attempt: Retry attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = min(
            self.retry_config.INITIAL_BACKOFF * (self.retry_config.BACKOFF_MULTIPLIER ** attempt),
            self.retry_config.MAX_BACKOFF
        )
        # Add jitter to prevent thundering herd
        import random
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter
    
    def scrape_with_retry(self, url: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        Scrape URL with retry logic
        
        Args:
            url: URL to scrape
            metadata: Optional metadata
            
        Returns:
            Result dictionary with status and data
        """
        metadata = metadata or {}
        last_error = None
        
        for attempt in range(self.retry_config.MAX_RETRIES):
            try:
                logger.info(f"[{self.worker_id}] Attempt {attempt + 1}/{self.retry_config.MAX_RETRIES} for {url}")
                
                # Import here to avoid circular dependencies
                from scraper.scrapy_runner import run_spider
                
                # Run scraper
                result = run_spider(
                    url=url,
                    output_file=None,  # Don't save to file
                    wait_time=5
                )
                
                if result.get("status") == "success":
                    # Store in MongoDB
                    html_content = result.get("html", "")
                    doc_id = self.storage.store_raw_html(
                        url=url,
                        html_content=html_content,
                        status="success",
                        metadata={
                            **metadata,
                            "worker_id": self.worker_id,
                            "attempts": attempt + 1
                        }
                    )
                    
                    logger.success(f"[{self.worker_id}] Successfully scraped {url} (attempts: {attempt + 1})")
                    self.stats["succeeded"] += 1
                    
                    return {
                        "status": "success",
                        "url": url,
                        "doc_id": doc_id,
                        "attempts": attempt + 1,
                        "html_length": len(html_content)
                    }
                else:
                    raise Exception(f"Scraping failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[{self.worker_id}] Attempt {attempt + 1} failed for {url}: {e}")
                
                if attempt < self.retry_config.MAX_RETRIES - 1:
                    # Calculate backoff and retry
                    delay = self.exponential_backoff(attempt)
                    logger.info(f"[{self.worker_id}] Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                    self.stats["retried"] += 1
                else:
                    # Max retries reached, send to dead letter queue
                    logger.error(f"[{self.worker_id}] Max retries reached for {url}")
                    self.send_to_dead_letter_queue(url, last_error, metadata)
                    self.stats["failed"] += 1
                    self.stats["dead_lettered"] += 1
                    
                    return {
                        "status": "failed",
                        "url": url,
                        "error": last_error,
                        "attempts": self.retry_config.MAX_RETRIES
                    }
        
        return {
            "status": "failed",
            "url": url,
            "error": "Unknown error after all retries",
            "attempts": self.retry_config.MAX_RETRIES
        }
    
    def send_to_dead_letter_queue(self, url: str, error: str, metadata: Dict = None):
        """
        Send failed task to dead letter queue for manual inspection
        
        Args:
            url: Failed URL
            error: Error message
            metadata: Task metadata
        """
        try:
            dead_letter_doc = {
                "url": url,
                "error": error,
                "metadata": metadata or {},
                "worker_id": self.worker_id,
                "failed_at": datetime.utcnow(),
                "retry_count": self.retry_config.MAX_RETRIES,
                "status": "dead_letter"
            }
            
            # Store in MongoDB dead_letter collection
            self.storage.db.dead_letter_queue.insert_one(dead_letter_doc)
            logger.warning(f"[{self.worker_id}] Sent to dead letter queue: {url}")
            
            # Also publish to Kafka dead letter topic
            try:
                self.url_manager.producer.send(
                    'dead-letter-queue',
                    value={
                        "url": url,
                        "error": error,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            except Exception as kafka_error:
                logger.error(f"Failed to publish to Kafka DLQ: {kafka_error}")
                
        except Exception as e:
            logger.error(f"[{self.worker_id}] Failed to send to dead letter queue: {e}")
    
    def process_task(self, task: Dict) -> Dict[str, Any]:
        """
        Process a scraping task with fault tolerance
        
        Args:
            task: Task dictionary with url and metadata
            
        Returns:
            Result dictionary
        """
        self.stats["processed"] += 1
        url = task.get("url")
        metadata = task.get("metadata", {})
        
        logger.info(f"[{self.worker_id}] Processing task: {url}")
        result = self.scrape_with_retry(url, metadata)
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        return {
            "worker_id": self.worker_id,
            "stats": self.stats,
            "success_rate": (
                self.stats["succeeded"] / self.stats["processed"] 
                if self.stats["processed"] > 0 else 0
            ) * 100,
            "retry_rate": (
                self.stats["retried"] / self.stats["processed"]
                if self.stats["processed"] > 0 else 0
            ) * 100
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Health check for monitoring
        
        Returns:
            Health status dictionary
        """
        try:
            # Check MongoDB connection
            mongo_healthy = self.storage.client.server_info() is not None
            
            # Check Kafka connection
            kafka_healthy = self.url_manager.producer is not None
            
            overall_health = mongo_healthy and kafka_healthy
            
            return {
                "status": "healthy" if overall_health else "degraded",
                "worker_id": self.worker_id,
                "mongodb": "connected" if mongo_healthy else "disconnected",
                "kafka": "connected" if kafka_healthy else "disconnected",
                "stats": self.stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "worker_id": self.worker_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


def test_fault_tolerance():
    """Test fault tolerance with intentional failures"""
    scraper = FaultTolerantScraper("test-ft-scraper")
    
    print("Testing Fault Tolerance")
    print("=" * 50)
    
    # Test 1: Valid URL
    print("\n1. Testing valid URL...")
    result1 = scraper.process_task({
        "url": "https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=PTS",
        "metadata": {"test": "valid_url"}
    })
    print(f"Result: {result1['status']}")
    
    # Test 2: Invalid URL (should retry and fail)
    print("\n2. Testing invalid URL (will retry 3 times)...")
    result2 = scraper.process_task({
        "url": "https://invalid-nba-url-12345.com/nonexistent",
        "metadata": {"test": "invalid_url"}
    })
    print(f"Result: {result2['status']}")
    
    # Print statistics
    print("\n" + "=" * 50)
    print("Worker Statistics:")
    stats = scraper.get_stats()
    print(json.dumps(stats, indent=2))
    
    # Health check
    print("\n" + "=" * 50)
    print("Health Check:")
    health = scraper.health_check()
    print(json.dumps(health, indent=2))


if __name__ == "__main__":
    test_fault_tolerance()
