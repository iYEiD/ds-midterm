"""
Kafka-based Processor Worker
Consumes scraping results from Kafka, processes them, and stores in MongoDB/ChromaDB
"""
import sys
import json
import signal
from pathlib import Path
from typing import Dict
from loguru import logger
from kafka import KafkaConsumer

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from scraper.storage import get_storage
from processor.html_parser import NBATableParser
from processor.normalizer import StatsNormalizer
from rag.embedder import StatsEmbedder
from rag.vector_store import get_vector_store

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)


class ProcessorWorker:
    """Worker that processes scraped data and creates embeddings"""
    
    def __init__(self, worker_id: str = "processor-1"):
        """
        Initialize processor worker
        
        Args:
            worker_id: Unique identifier for this worker
        """
        self.worker_id = worker_id
        self.storage = get_storage()
        self.parser = NBATableParser()
        self.normalizer = StatsNormalizer()
        self.embedder = StatsEmbedder()
        self.vector_store = get_vector_store()
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"ProcessorWorker {worker_id} initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def process_scraped_data(self, result: Dict) -> Dict:
        """
        Process scraped data result
        
        Args:
            result: Scraping result from Kafka
            
        Returns:
            Processing result
        """
        url = result.get('url')
        status = result.get('status')
        
        logger.info(f"[{self.worker_id}] Processing result for: {url}")
        
        # Skip failed scrapes
        if status != 'success':
            logger.warning(f"Skipping failed scrape: {url}")
            return {
                'status': 'skipped',
                'url': url,
                'reason': 'scraping_failed',
                'worker_id': self.worker_id
            }
        
        try:
            # Get raw data from MongoDB
            raw_doc = self.storage.raw_data.find_one({'url': url})
            
            if not raw_doc:
                logger.error(f"Raw data not found for {url}")
                return {
                    'status': 'failed',
                    'url': url,
                    'error': 'Raw data not found',
                    'worker_id': self.worker_id
                }
            
            html_content = raw_doc.get('html_content', '')
            
            # Parse the data (it's JSON from Scrapy)
            try:
                scraped_json = json.loads(html_content)
            except json.JSONDecodeError:
                # If it's actual HTML, parse it
                tables = self.parser.parse_html(html_content)
                scraped_json = {'data': tables[0]['data'], 'headers': tables[0]['headers']} if tables else {}
            
            data = scraped_json.get('data', [])
            
            if not data:
                logger.warning(f"No data found in {url}")
                return {
                    'status': 'no_data',
                    'url': url,
                    'worker_id': self.worker_id
                }
            
            # Process each player
            players_processed = 0
            players_embedded = []
            
            for player_data in data:
                player_name = player_data.get('PLAYER', '')
                
                if not player_name:
                    continue
                
                # Normalize stats
                normalized = self.normalizer.normalize_player_stats(
                    player_name=player_name,
                    stats=player_data,
                    metadata={
                        'season_type': 'Regular Season',
                        'source_url': url
                    }
                )
                
                if not self.normalizer.validate_stats(normalized):
                    logger.warning(f"Invalid stats for {player_name}")
                    continue
                
                # Store processed stats in MongoDB
                self.storage.store_processed_stats(
                    player_name=normalized['player_name'],
                    stats=normalized['stats'],
                    season_type='Regular Season'
                )
                
                players_processed += 1
                
                # Prepare for embedding
                players_embedded.append({
                    'player_name': normalized['player_name'],
                    'stats': normalized['stats'],
                    'metadata': normalized['metadata']
                })
            
            # Generate embeddings in batch
            if players_embedded:
                logger.info(f"Generating embeddings for {len(players_embedded)} players...")
                embedded_players = self.embedder.embed_players_batch(players_embedded)
                
                if embedded_players:
                    # Prepare for ChromaDB
                    ids = [f"player_{p['player_name'].replace(' ', '_')}" 
                           for p in embedded_players]
                    embeddings = [p['embedding'] for p in embedded_players]
                    documents = [p['text'] for p in embedded_players]
                    metadatas = [
                        {'player': p['player_name'], 'season_type': p['metadata'].get('season_type', 'Regular Season')}
                        for p in embedded_players
                    ]
                    
                    # Store in ChromaDB
                    success = self.vector_store.add_embeddings(
                        ids, embeddings, documents, metadatas
                    )
                    
                    if success:
                        logger.info(f"Added {len(embedded_players)} embeddings to ChromaDB")
            
            return {
                'status': 'success',
                'url': url,
                'players_processed': players_processed,
                'players_embedded': len(players_embedded),
                'worker_id': self.worker_id
            }
            
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            return {
                'status': 'failed',
                'url': url,
                'error': str(e),
                'worker_id': self.worker_id
            }
    
    def run(self):
        """
        Main worker loop - consume results from Kafka
        """
        logger.info(f"[{self.worker_id}] Starting processor loop...")
        
        # Create Kafka consumer
        try:
            consumer = KafkaConsumer(
                settings.KAFKA_SCRAPING_RESULTS_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id='processor-workers',
                auto_offset_reset='earliest',
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            
            logger.info(f"[{self.worker_id}] Listening for results on topic: {settings.KAFKA_SCRAPING_RESULTS_TOPIC}")
            
        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {e}")
            return
        
        try:
            for message in consumer:
                if not self.running:
                    logger.info("Worker shutting down...")
                    break
                
                try:
                    # Parse message
                    result = message.value
                    logger.info(f"[{self.worker_id}] Received result: {result.get('url', 'Unknown')}")
                    
                    # Process the result
                    processing_result = self.process_scraped_data(result)
                    
                    logger.info(f"[{self.worker_id}] Processing completed: {processing_result['status']}")
                    
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
    
    parser = argparse.ArgumentParser(description='Kafka Processor Worker')
    parser.add_argument('--worker-id', type=str, default='processor-1',
                       help='Unique worker ID')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"KAFKA PROCESSOR WORKER - {args.worker_id}")
    print('='*60)
    
    worker = ProcessorWorker(worker_id=args.worker_id)
    worker.run()


if __name__ == "__main__":
    main()
