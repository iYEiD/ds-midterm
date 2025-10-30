"""
Kafka URL manager for distributed scraping
Handles producing and consuming URLs for scraping tasks
"""
from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.structs import TopicPartition
from kafka.errors import KafkaError
from typing import List, Optional, Callable
import json
from loguru import logger
import sys

from config import settings

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)


class KafkaURLManager:
    """Manages URL distribution via Kafka"""
    
    def __init__(self):
        """Initialize Kafka producer and consumer"""
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.scraping_topic = settings.KAFKA_SCRAPING_TASKS_TOPIC
        self.results_topic = settings.KAFKA_SCRAPING_RESULTS_TOPIC
        
        # Initialize producer
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Wait for all replicas
                retries=3
            )
            logger.info("Kafka producer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None
    
    def submit_url(self, url: str, metadata: Optional[dict] = None, 
                   priority: int = 0) -> bool:
        """
        Submit a URL to the scraping queue
        
        Args:
            url: URL to scrape
            metadata: Additional metadata for the scraping task
            priority: Priority level (higher = more important)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False
        
        try:
            message = {
                "url": url,
                "metadata": metadata or {},
                "priority": priority
            }
            
            future = self.producer.send(self.scraping_topic, value=message)
            # Wait for send to complete
            result = future.get(timeout=10)
            
            logger.info(f"Submitted URL to Kafka: {url}")
            return True
            
        except KafkaError as e:
            logger.error(f"Kafka error submitting URL {url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error submitting URL {url}: {e}")
            return False
    
    def submit_urls_batch(self, urls: List[str], metadata: Optional[dict] = None) -> int:
        """
        Submit multiple URLs to the scraping queue
        
        Args:
            urls: List of URLs to scrape
            metadata: Shared metadata for all URLs
            
        Returns:
            Number of successfully submitted URLs
        """
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return 0
        
        success_count = 0
        for url in urls:
            if self.submit_url(url, metadata):
                success_count += 1
        
        # Flush to ensure all messages are sent
        self.producer.flush()
        logger.info(f"Submitted {success_count}/{len(urls)} URLs to Kafka")
        
        return success_count
    
    def submit_result(self, url: str, status: str, data: Optional[dict] = None) -> bool:
        """
        Submit scraping result to results topic
        
        Args:
            url: The scraped URL
            status: Result status (success/failed)
            data: Result data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False
        
        try:
            message = {
                "url": url,
                "status": status,
                "data": data or {}
            }
            
            future = self.producer.send(self.results_topic, value=message)
            result = future.get(timeout=10)
            
            logger.debug(f"Submitted result for URL: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting result for {url}: {e}")
            return False
    
    def create_consumer(self, group_id: str = "scraper-workers", 
                       auto_offset_reset: str = 'earliest') -> Optional[KafkaConsumer]:
        """
        Create a Kafka consumer for scraping tasks
        
        Args:
            group_id: Consumer group ID
            auto_offset_reset: Where to start reading ('earliest' or 'latest')
            
        Returns:
            KafkaConsumer instance or None if failed
        """
        try:
            consumer = KafkaConsumer(
                self.scraping_topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            logger.info(f"Created Kafka consumer for group: {group_id}")
            return consumer
            
        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {e}")
            return None
    
    def consume_urls(self, callback: Callable, group_id: str = "scraper-workers",
                     max_messages: Optional[int] = None):
        """
        Consume URLs from Kafka and process them with callback
        
        Args:
            callback: Function to call for each URL message
            group_id: Consumer group ID
            max_messages: Maximum number of messages to process (None = infinite)
        """
        consumer = self.create_consumer(group_id)
        if not consumer:
            logger.error("Failed to create consumer")
            return
        
        try:
            message_count = 0
            logger.info("Starting to consume URLs from Kafka...")
            
            for message in consumer:
                try:
                    callback(message.value)
                    message_count += 1
                    
                    if max_messages and message_count >= max_messages:
                        logger.info(f"Reached max messages limit: {max_messages}")
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        finally:
            consumer.close()
            logger.info("Kafka consumer closed")
    
    def get_pending_count(self) -> int:
        """
        Get approximate count of pending messages in scraping queue
        
        Returns:
            Number of pending messages
        """
        try:
            # Create consumer WITHOUT subscribing - use manual assignment only
            consumer = KafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                group_id='count-checker',
                auto_offset_reset='earliest',
                enable_auto_commit=False
            )
            
            # Get partition info
            partitions = consumer.partitions_for_topic(self.scraping_topic)
            if not partitions:
                consumer.close()
                return 0
            
            # Manually assign all partitions
            topic_partitions = [TopicPartition(self.scraping_topic, p) for p in partitions]
            consumer.assign(topic_partitions)
            
            # Calculate total pending across all partitions
            pending = 0
            end_offsets = consumer.end_offsets(topic_partitions)
            
            for tp in topic_partitions:
                # Get committed offset for this partition (what's been consumed)
                committed = consumer.committed(tp)
                committed_offset = committed if committed is not None else 0
                
                # Get high water mark (total messages)
                end_offset = end_offsets[tp]
                
                # Pending = messages not yet consumed
                pending += (end_offset - committed_offset)
            
            consumer.close()
            return pending
            
        except Exception as e:
            logger.error(f"Error getting pending count: {e}")
            return 0
    
    def close(self):
        """Close Kafka connections"""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")


# Global instance
_url_manager = None

def get_url_manager() -> KafkaURLManager:
    """Get or create Kafka URL manager instance"""
    global _url_manager
    if _url_manager is None:
        _url_manager = KafkaURLManager()
    return _url_manager
