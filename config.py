"""
Configuration module for the distributed scraper
Loads environment variables and provides centralized config
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # MongoDB Configuration
    MONGO_URI: str = "mongodb://localhost:27017/"
    MONGO_DB_NAME: str = "nba_scraper"
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_SCRAPING_TASKS_TOPIC: str = "scraping-tasks"
    KAFKA_SCRAPING_RESULTS_TOPIC: str = "scraping-results"
    KAFKA_PROCESSING_TASKS_TOPIC: str = "processing-tasks"
    
    # Ray Configuration
    RAY_ADDRESS: Optional[str] = None  # None means local mode, set to "ray://localhost:10001" for cluster
    RAY_DASHBOARD_PORT: int = 8265
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # ChromaDB Configuration
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    CHROMA_COLLECTION_NAME: str = "nba_stats_embeddings"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RATE_LIMIT: str = "100/hour"
    
    # Scraping Configuration
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (compatible; NBA-Stats-Scraper/1.0)"
    SCRAPER_DELAY: float = 1.0
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_TIMEOUT: int = 30
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings
