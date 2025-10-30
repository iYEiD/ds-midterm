"""
Distributed scraping with Ray
Enables parallel scraping across multiple workers
"""
import ray
from typing import List, Dict, Optional
from loguru import logger
import sys

from config import settings
from scraper.nba_scraper import NBAStatsScraper
from scraper.storage import get_storage
from scraper.url_manager import get_url_manager

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)


@ray.remote
class ScraperWorker:
    """Ray actor for scraping tasks"""
    
    def __init__(self, worker_id: int):
        """
        Initialize scraper worker
        
        Args:
            worker_id: Unique worker identifier
        """
        self.worker_id = worker_id
        self.scraper = NBAStatsScraper()
        logger.info(f"ScraperWorker {worker_id} initialized")
    
    def scrape_url(self, url: str) -> Dict:
        """
        Scrape a single URL
        
        Args:
            url: URL to scrape
            
        Returns:
            Scraping result dictionary
        """
        logger.info(f"Worker {self.worker_id} scraping: {url}")
        
        try:
            result = self.scraper.scrape_and_parse(url)
            
            if result:
                result["worker_id"] = self.worker_id
                return result
            else:
                return {
                    "url": url,
                    "status": "failed",
                    "error": "Unknown error",
                    "worker_id": self.worker_id
                }
                
        except Exception as e:
            logger.error(f"Worker {self.worker_id} error scraping {url}: {e}")
            return {
                "url": url,
                "status": "failed",
                "error": str(e),
                "worker_id": self.worker_id
            }
    
    def scrape_urls_batch(self, urls: List[str]) -> List[Dict]:
        """
        Scrape multiple URLs sequentially
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of scraping results
        """
        results = []
        for url in urls:
            result = self.scrape_url(url)
            results.append(result)
        return results
    
    def get_worker_id(self) -> int:
        """Get worker ID"""
        return self.worker_id


class DistributedScraper:
    """Manages distributed scraping with Ray"""
    
    def __init__(self, num_workers: int = 4, init_ray: bool = True):
        """
        Initialize distributed scraper
        
        Args:
            num_workers: Number of parallel workers
            init_ray: Whether to initialize Ray (False if already initialized)
        """
        self.num_workers = num_workers
        
        # Initialize Ray if needed
        if init_ray:
            if ray.is_initialized():
                logger.info("Ray already initialized")
            else:
                if settings.RAY_ADDRESS:
                    ray.init(address=settings.RAY_ADDRESS)
                    logger.info(f"Connected to Ray cluster at {settings.RAY_ADDRESS}")
                else:
                    ray.init(ignore_reinit_error=True)
                    logger.info("Ray initialized in local mode")
        
        # Create worker pool
        self.workers = [ScraperWorker.remote(i) for i in range(num_workers)]
        logger.info(f"Created {num_workers} scraper workers")
    
    def scrape_urls_parallel(self, urls: List[str]) -> List[Dict]:
        """
        Scrape multiple URLs in parallel using Ray workers
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of scraping results
        """
        if not urls:
            logger.warning("No URLs provided for scraping")
            return []
        
        logger.info(f"Scraping {len(urls)} URLs with {self.num_workers} workers")
        
        # Distribute URLs across workers
        chunk_size = max(1, len(urls) // self.num_workers)
        url_chunks = [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]
        
        # Dispatch tasks to workers
        futures = []
        for i, url_chunk in enumerate(url_chunks):
            worker = self.workers[i % self.num_workers]
            future = worker.scrape_urls_batch.remote(url_chunk)
            futures.append(future)
        
        # Collect results
        all_results = []
        for future in futures:
            try:
                results = ray.get(future)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Error getting results from worker: {e}")
        
        # Log summary
        success_count = sum(1 for r in all_results if r.get("status") in ["success", "exists"])
        logger.info(f"Completed scraping: {success_count}/{len(all_results)} successful")
        
        return all_results
    
    def scrape_urls_from_kafka(self, max_messages: int = 10):
        """
        Consume URLs from Kafka and scrape them in parallel
        
        Args:
            max_messages: Maximum number of URLs to process
        """
        url_manager = get_url_manager()
        
        # Collect URLs from Kafka
        urls_to_scrape = []
        
        def collect_url(message: Dict):
            url = message.get("url")
            if url:
                urls_to_scrape.append(url)
                logger.info(f"Collected URL from Kafka: {url}")
        
        # Consume messages
        consumer = url_manager.create_consumer(group_id="distributed-scraper")
        if not consumer:
            logger.error("Failed to create Kafka consumer")
            return
        
        try:
            for message in consumer:
                collect_url(message.value)
                if len(urls_to_scrape) >= max_messages:
                    break
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            consumer.close()
        
        # Scrape collected URLs
        if urls_to_scrape:
            logger.info(f"Scraping {len(urls_to_scrape)} URLs from Kafka")
            results = self.scrape_urls_parallel(urls_to_scrape)
            
            # Submit results back to Kafka
            for result in results:
                url_manager.submit_result(
                    url=result["url"],
                    status=result["status"],
                    data=result
                )
        else:
            logger.info("No URLs to scrape from Kafka")
    
    def get_cluster_info(self) -> Dict:
        """
        Get information about the Ray cluster
        
        Returns:
            Dictionary with cluster information
        """
        try:
            return {
                "num_workers": self.num_workers,
                "ray_initialized": ray.is_initialized(),
                "available_resources": ray.available_resources() if ray.is_initialized() else {}
            }
        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            return {}
    
    def shutdown(self):
        """Shutdown Ray and cleanup resources"""
        try:
            # Kill all workers
            for worker in self.workers:
                ray.kill(worker)
            logger.info("All workers terminated")
        except Exception as e:
            logger.error(f"Error shutting down workers: {e}")


def test_distributed_scraping():
    """Test function for distributed scraping"""
    
    # Sample NBA stats URLs
    test_urls = [
        "https://www.nba.com/stats/alltime-leaders",
        "https://www.nba.com/stats/leaders",
    ]
    
    logger.info("Testing distributed scraping...")
    
    # Create distributed scraper
    scraper = DistributedScraper(num_workers=2)
    
    try:
        # Get cluster info
        info = scraper.get_cluster_info()
        logger.info(f"Cluster info: {info}")
        
        # Scrape URLs
        results = scraper.scrape_urls_parallel(test_urls)
        
        # Print results
        print("\n" + "="*60)
        print("DISTRIBUTED SCRAPING RESULTS")
        print("="*60)
        for result in results:
            print(f"\nURL: {result['url']}")
            print(f"Status: {result['status']}")
            print(f"Worker: {result.get('worker_id', 'N/A')}")
            print(f"Rows parsed: {result.get('row_count', 0)}")
            print(f"From cache: {result.get('from_cache', False)}")
        
        print("\n" + "="*60)
        
    finally:
        scraper.shutdown()


if __name__ == "__main__":
    test_distributed_scraping()
