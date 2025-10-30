"""
Distributed data processing with Ray
Processes scraped HTML data in parallel
"""
import ray
from typing import List, Dict, Optional
from loguru import logger
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from scraper.storage import get_storage
from processor.html_parser import NBATableParser
from processor.normalizer import StatsNormalizer

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)


@ray.remote
class ProcessorWorker:
    """Ray actor for processing tasks"""
    
    def __init__(self, worker_id: int):
        """
        Initialize processor worker
        
        Args:
            worker_id: Unique worker identifier
        """
        self.worker_id = worker_id
        self.parser = NBATableParser()
        self.normalizer = StatsNormalizer()
        self.storage = get_storage()
        logger.info(f"ProcessorWorker {worker_id} initialized")
    
    def process_raw_data(self, doc_id: str, raw_doc: Dict) -> Dict:
        """
        Process raw scraped data
        
        Args:
            doc_id: Document ID
            raw_doc: Raw data document from MongoDB
            
        Returns:
            Processing result dictionary
        """
        logger.info(f"Worker {self.worker_id} processing document: {doc_id}")
        
        try:
            url = raw_doc.get('url', '')
            html_content = raw_doc.get('html_content', '')
            
            # Parse HTML
            tables = self.parser.parse_html(html_content)
            
            if not tables:
                return {
                    'status': 'failed',
                    'error': 'No tables found',
                    'doc_id': doc_id,
                    'processed_count': 0
                }
            
            processed_count = 0
            
            # Process each table
            for table in tables:
                # Parse player stats
                players = self.parser.parse_player_stats(table)
                
                # Normalize and store
                for player in players:
                    player_name = player.get('player_name', '')
                    stats = player.get('stats', {})
                    
                    if not player_name:
                        continue
                    
                    # Normalize stats
                    normalized = self.normalizer.normalize_player_stats(
                        player_name=player_name,
                        stats=stats,
                        metadata={
                            'season_type': 'Regular Season',
                            'source_url': url,
                            'table_index': table.get('table_index', 0)
                        }
                    )
                    
                    # Validate
                    if self.normalizer.validate_stats(normalized):
                        # Store in MongoDB
                        self.storage.store_processed_stats(
                            player_name=normalized['player_name'],
                            stats=normalized['stats'],
                            season_type=normalized['metadata']['season_type']
                        )
                        processed_count += 1
            
            return {
                'status': 'success',
                'doc_id': doc_id,
                'processed_count': processed_count,
                'worker_id': self.worker_id
            }
            
        except Exception as e:
            logger.error(f"Worker {self.worker_id} error processing {doc_id}: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'doc_id': doc_id,
                'processed_count': 0
            }


class DistributedProcessor:
    """Distributed processor using Ray"""
    
    def __init__(self, num_workers: int = 4):
        """
        Initialize distributed processor
        
        Args:
            num_workers: Number of Ray worker actors
        """
        self.num_workers = num_workers
        self.storage = get_storage()
        
        # Initialize Ray if not already initialized
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
            logger.info("Ray initialized in local mode")
        
        # Create worker actors
        self.workers = [
            ProcessorWorker.remote(i) for i in range(num_workers)
        ]
        logger.info(f"Created {num_workers} processor workers")
    
    def process_batch(self, limit: int = 100) -> Dict:
        """
        Process a batch of raw documents
        
        Args:
            limit: Maximum number of documents to process
            
        Returns:
            Processing statistics
        """
        logger.info(f"Starting batch processing (limit: {limit})")
        
        # Get unprocessed documents
        raw_docs = list(self.storage.raw_data.find().limit(limit))
        
        if not raw_docs:
            logger.info("No documents to process")
            return {
                'status': 'success',
                'processed': 0,
                'failed': 0,
                'total': 0
            }
        
        logger.info(f"Found {len(raw_docs)} documents to process")
        
        # Distribute work among workers
        tasks = []
        for idx, doc in enumerate(raw_docs):
            worker_idx = idx % self.num_workers
            doc_id = str(doc.get('_id', ''))
            
            # Submit task to worker
            task = self.workers[worker_idx].process_raw_data.remote(doc_id, doc)
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = ray.get(tasks)
        
        # Aggregate statistics
        stats = {
            'status': 'success',
            'processed': sum(1 for r in results if r['status'] == 'success'),
            'failed': sum(1 for r in results if r['status'] == 'failed'),
            'total': len(results),
            'players_processed': sum(r.get('processed_count', 0) for r in results)
        }
        
        logger.info(f"Batch processing complete: {stats}")
        return stats
    
    def process_all(self) -> Dict:
        """
        Process all unprocessed documents
        
        Returns:
            Processing statistics
        """
        total_stats = {
            'processed': 0,
            'failed': 0,
            'total': 0,
            'players_processed': 0
        }
        
        batch_size = 100
        while True:
            batch_stats = self.process_batch(limit=batch_size)
            
            if batch_stats['total'] == 0:
                break
            
            # Aggregate stats
            total_stats['processed'] += batch_stats['processed']
            total_stats['failed'] += batch_stats['failed']
            total_stats['total'] += batch_stats['total']
            total_stats['players_processed'] += batch_stats['players_processed']
        
        total_stats['status'] = 'success'
        logger.info(f"All processing complete: {total_stats}")
        return total_stats
    
    def shutdown(self):
        """Shutdown Ray"""
        if ray.is_initialized():
            ray.shutdown()
            logger.info("Ray shutdown complete")


def test_distributed_processor():
    """Test the distributed processor"""
    print(f"\n{'='*60}")
    print("DISTRIBUTED PROCESSOR TEST")
    print('='*60)
    
    # Initialize processor
    processor = DistributedProcessor(num_workers=2)
    
    # Process a small batch
    print("\nProcessing batch...")
    stats = processor.process_batch(limit=10)
    
    print(f"\nResults:")
    print(f"  Status: {stats['status']}")
    print(f"  Processed: {stats['processed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Total: {stats['total']}")
    print(f"  Players processed: {stats.get('players_processed', 0)}")
    
    # Shutdown
    processor.shutdown()


if __name__ == "__main__":
    test_distributed_processor()
