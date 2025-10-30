"""
End-to-End Integration Test for Distributed System
Tests the complete Kafka-based workflow
"""
import sys
import time
import subprocess
import signal
from pathlib import Path
from typing import List
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from scraper.storage import get_storage
from rag.vector_store import get_vector_store
from orchestrator import JobOrchestrator

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")


class DistributedSystemTest:
    """End-to-end test for the distributed system"""
    
    def __init__(self):
        """Initialize test"""
        self.storage = get_storage()
        self.vector_store = get_vector_store()
        self.orchestrator = JobOrchestrator()
        self.worker_processes = []
    
    def start_workers(self, num_scrapers: int = 2, num_processors: int = 2):
        """
        Start worker processes
        
        Args:
            num_scrapers: Number of scraper workers
            num_processors: Number of processor workers
        """
        logger.info(f"Starting {num_scrapers} scraper workers and {num_processors} processor workers...")
        
        # Start scraper workers
        for i in range(num_scrapers):
            worker_id = f"scraper-{i+1}"
            cmd = [
                sys.executable,
                str(project_root / "scraper" / "kafka_scraper_worker.py"),
                "--worker-id", worker_id
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.worker_processes.append({
                'type': 'scraper',
                'id': worker_id,
                'process': process
            })
            
            logger.info(f"Started scraper worker: {worker_id} (PID: {process.pid})")
        
        # Start processor workers
        for i in range(num_processors):
            worker_id = f"processor-{i+1}"
            cmd = [
                sys.executable,
                str(project_root / "processor" / "kafka_processor_worker.py"),
                "--worker-id", worker_id
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.worker_processes.append({
                'type': 'processor',
                'id': worker_id,
                'process': process
            })
            
            logger.info(f"Started processor worker: {worker_id} (PID: {process.pid})")
        
        # Give workers time to start
        time.sleep(5)
        logger.info("All workers started")
    
    def stop_workers(self):
        """Stop all worker processes"""
        logger.info("Stopping workers...")
        
        for worker in self.worker_processes:
            try:
                worker['process'].send_signal(signal.SIGINT)
                worker['process'].wait(timeout=5)
                logger.info(f"Stopped {worker['type']} worker: {worker['id']}")
            except subprocess.TimeoutExpired:
                worker['process'].kill()
                logger.warning(f"Killed {worker['type']} worker: {worker['id']}")
            except Exception as e:
                logger.error(f"Error stopping worker {worker['id']}: {e}")
        
        self.worker_processes = []
    
    def get_initial_stats(self) -> dict:
        """Get initial system stats"""
        mongo_stats = self.storage.get_stats_count()
        vector_count = self.vector_store.count()
        
        return {
            'mongodb': mongo_stats,
            'chromadb': vector_count
        }
    
    def verify_results(self, initial_stats: dict, expected_urls: int) -> dict:
        """
        Verify test results
        
        Args:
            initial_stats: Stats before test
            expected_urls: Expected number of URLs processed
            
        Returns:
            Verification results
        """
        logger.info("Verifying results...")
        
        # Get final stats
        mongo_stats = self.storage.get_stats_count()
        vector_count = self.vector_store.count()
        
        # Calculate differences
        new_raw = mongo_stats['raw_data_count'] - initial_stats['mongodb']['raw_data_count']
        new_processed = mongo_stats['processed_stats_count'] - initial_stats['mongodb']['processed_stats_count']
        new_embeddings = vector_count - initial_stats['chromadb']
        
        results = {
            'new_raw_documents': new_raw,
            'new_processed_stats': new_processed,
            'new_embeddings': new_embeddings,
            'expected_urls': expected_urls,
            'success': new_raw >= expected_urls and new_processed > 0 and new_embeddings > 0
        }
        
        logger.info(f"Results:")
        logger.info(f"  New raw documents: {new_raw} (expected >= {expected_urls})")
        logger.info(f"  New processed stats: {new_processed}")
        logger.info(f"  New embeddings: {new_embeddings}")
        logger.info(f"  Success: {results['success']}")
        
        return results
    
    def run_test(self, test_urls: List[str], timeout: int = 180):
        """
        Run end-to-end test
        
        Args:
            test_urls: URLs to test with
            timeout: Test timeout in seconds
            
        Returns:
            Test results
        """
        print(f"\n{'='*60}")
        print("DISTRIBUTED SYSTEM E2E TEST")
        print('='*60)
        
        # Get initial stats
        initial_stats = self.get_initial_stats()
        logger.info(f"Initial stats: MongoDB={initial_stats['mongodb']}, ChromaDB={initial_stats['chromadb']}")
        
        # Start workers
        self.start_workers(num_scrapers=2, num_processors=2)
        
        try:
            # Submit job
            logger.info(f"\nSubmitting {len(test_urls)} URLs...")
            result = self.orchestrator.run_scraping_job(
                urls=test_urls,
                metadata={'test': 'e2e', 'timestamp': time.time()},
                monitor=True,
                timeout=timeout
            )
            
            logger.info(f"Job result: {result['status']}")
            
            # Wait a bit for processing to complete
            logger.info("Waiting for processing to complete...")
            time.sleep(10)
            
            # Verify results
            verification = self.verify_results(initial_stats, len(test_urls))
            
            print(f"\n{'='*60}")
            print("TEST RESULTS")
            print('='*60)
            print(f"Status: {'✓ PASSED' if verification['success'] else '✗ FAILED'}")
            print(f"New raw documents: {verification['new_raw_documents']}")
            print(f"New processed stats: {verification['new_processed_stats']}")
            print(f"New embeddings: {verification['new_embeddings']}")
            print('='*60)
            
            return verification
            
        finally:
            # Stop workers
            self.stop_workers()


def main():
    """Main entry point"""
    # Test URLs
    test_urls = [
        "https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=BLK",
    ]
    
    # Run test
    test = DistributedSystemTest()
    results = test.run_test(test_urls, timeout=120)
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)


if __name__ == "__main__":
    main()
