"""
Database connection and storage module for MongoDB
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from typing import Dict, List, Optional, Any
from loguru import logger
import sys

from config import settings

# Configure loguru logger
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)
logger.add(settings.LOG_FILE, rotation="500 MB", level=settings.LOG_LEVEL)


class MongoDBStorage:
    """MongoDB storage handler with connection pooling"""
    
    def __init__(self):
        """Initialize MongoDB connection"""
        self.client = MongoClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DB_NAME]
        logger.info(f"Connected to MongoDB: {settings.MONGO_DB_NAME}")
        
        # Collections
        self.raw_data = self.db.raw_scraped_data
        self.processed_data = self.db.processed_stats
        self.metadata = self.db.scraping_metadata
        self.query_history = self.db.query_history
        
    def store_raw_html(self, url: str, html_content: str, status: str = "success", 
                       metadata: Optional[Dict] = None) -> Optional[str]:
        """
        Store raw scraped HTML data
        
        Args:
            url: The scraped URL
            html_content: Raw HTML content
            status: Scraping status (success/failed)
            metadata: Additional metadata
            
        Returns:
            Document ID if successful, None otherwise
        """
        try:
            document = {
                "url": url,
                "html_content": html_content,
                "status": status,
                "timestamp": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
            result = self.raw_data.insert_one(document)
            logger.info(f"Stored raw HTML for URL: {url}")
            return str(result.inserted_id)
            
        except DuplicateKeyError:
            logger.warning(f"URL already exists in database: {url}")
            # Update existing document
            self.raw_data.update_one(
                {"url": url},
                {
                    "$set": {
                        "html_content": html_content,
                        "status": status,
                        "timestamp": datetime.utcnow(),
                        "metadata": metadata or {}
                    }
                }
            )
            return None
        except Exception as e:
            logger.error(f"Error storing raw HTML for {url}: {e}")
            return None
    
    def get_raw_html(self, url: str) -> Optional[Dict]:
        """
        Retrieve raw HTML data by URL
        
        Args:
            url: The URL to retrieve
            
        Returns:
            Document if found, None otherwise
        """
        try:
            document = self.raw_data.find_one({"url": url})
            return document
        except Exception as e:
            logger.error(f"Error retrieving raw HTML for {url}: {e}")
            return None
    
    def url_exists(self, url: str) -> bool:
        """
        Check if URL has been scraped
        
        Args:
            url: The URL to check
            
        Returns:
            True if URL exists, False otherwise
        """
        try:
            return self.raw_data.count_documents({"url": url}) > 0
        except Exception as e:
            logger.error(f"Error checking URL existence for {url}: {e}")
            return False
    
    def store_processed_stats(self, player_name: str, stats: Dict, 
                             season_type: str = "Regular Season") -> Optional[str]:
        """
        Store processed player statistics
        
        Args:
            player_name: Player name
            stats: Dictionary of statistics
            season_type: Season type (Regular Season, Playoffs, etc.)
            
        Returns:
            Document ID if successful, None otherwise
        """
        try:
            document = {
                "player_name": player_name,
                "stats": stats,
                "metadata": {
                    "season_type": season_type,
                    "scraped_at": datetime.utcnow()
                }
            }
            
            # Use upsert to avoid duplicates
            result = self.processed_data.update_one(
                {
                    "player_name": player_name,
                    "metadata.season_type": season_type
                },
                {"$set": document},
                upsert=True
            )
            
            logger.info(f"Stored processed stats for player: {player_name}")
            return str(result.upserted_id) if result.upserted_id else "updated"
            
        except Exception as e:
            logger.error(f"Error storing processed stats for {player_name}: {e}")
            return None
    
    def get_player_stats(self, player_name: str, 
                         season_type: Optional[str] = None) -> List[Dict]:
        """
        Retrieve player statistics
        
        Args:
            player_name: Player name
            season_type: Optional season type filter
            
        Returns:
            List of matching documents
        """
        try:
            query = {"player_name": player_name}
            if season_type:
                query["metadata.season_type"] = season_type
            
            return list(self.processed_data.find(query))
        except Exception as e:
            logger.error(f"Error retrieving stats for {player_name}: {e}")
            return []
    
    def update_scraping_metadata(self, url: str, status: str = "scraped"):
        """
        Update metadata for scraped URL
        
        Args:
            url: The URL
            status: Scraping status
        """
        try:
            self.metadata.update_one(
                {"url": url},
                {
                    "$set": {
                        "url": url,
                        "last_scraped": datetime.utcnow(),
                        "status": status
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error updating metadata for {url}: {e}")
    
    def get_unscraped_urls(self, limit: int = 100) -> List[str]:
        """
        Get URLs that haven't been scraped recently
        
        Args:
            limit: Maximum number of URLs to return
            
        Returns:
            List of URLs
        """
        try:
            # Find URLs that either don't exist in metadata or are old
            # This is a placeholder - actual implementation would be more sophisticated
            return []
        except Exception as e:
            logger.error(f"Error getting unscraped URLs: {e}")
            return []
    
    def get_stats_count(self) -> Dict[str, int]:
        """
        Get statistics about stored data
        
        Returns:
            Dictionary with counts
        """
        try:
            return {
                "raw_data_count": self.raw_data.count_documents({}),
                "processed_stats_count": self.processed_data.count_documents({}),
                "unique_players": len(self.processed_data.distinct("player_name")),
                "metadata_count": self.metadata.count_documents({})
            }
        except Exception as e:
            logger.error(f"Error getting stats count: {e}")
            return {}
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()
        logger.info("Closed MongoDB connection")


# Global storage instance
_storage = None

def get_storage() -> MongoDBStorage:
    """Get or create MongoDB storage instance"""
    global _storage
    if _storage is None:
        _storage = MongoDBStorage()
    return _storage
