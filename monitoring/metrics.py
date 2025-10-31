"""
System metrics collector and reporter.
Tracks scraping rate, processing time, API latency, and resource usage.
"""
import time
import psutil
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, asdict
import json
from loguru import logger
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scraper.storage import get_storage
from rag.vector_store import get_vector_store


@dataclass
class MetricPoint:
    """Single metric measurement"""
    timestamp: datetime
    name: str
    value: float
    tags: Dict[str, str]
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "name": self.name,
            "value": self.value,
            "tags": self.tags
        }


class MetricsCollector:
    """Collects and aggregates system metrics"""
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize metrics collector
        
        Args:
            window_size: Number of recent metrics to keep
        """
        self.metrics = deque(maxlen=window_size)
        self.storage = get_storage()
        self.vector_store = get_vector_store()
        self.start_time = datetime.utcnow()
        
        logger.info("MetricsCollector initialized")
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric"""
        metric = MetricPoint(
            timestamp=datetime.utcnow(),
            name=name,
            value=value,
            tags=tags or {}
        )
        self.metrics.append(metric)
    
    def get_scraping_metrics(self) -> Dict[str, Any]:
        """Get scraping-related metrics"""
        try:
            stats = self.storage.get_stats_count()
            
            # Calculate rates
            uptime_hours = (datetime.utcnow() - self.start_time).total_seconds() / 3600
            
            return {
                "total_scraped": stats["raw_data_count"],
                "total_processed": stats["processed_stats_count"],
                "unique_players": stats["unique_players"],
                "scraping_rate": stats["raw_data_count"] / uptime_hours if uptime_hours > 0 else 0,
                "processing_rate": stats["processed_stats_count"] / uptime_hours if uptime_hours > 0 else 0,
                "embeddings_count": self.vector_store.count()
            }
        except Exception as e:
            logger.error(f"Error getting scraping metrics: {e}")
            return {}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "per_cpu": list(psutil.cpu_percent(interval=1, percpu=True))
                },
                "memory": {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "used_gb": memory.used / (1024**3),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": disk.total / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "percent": disk.percent
                },
                "process": {
                    "memory_mb": process_memory.rss / (1024**2),
                    "num_threads": process.num_threads(),
                    "num_fds": process.num_fds() if hasattr(process, 'num_fds') else None
                }
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """Get database connection and performance metrics"""
        try:
            # MongoDB metrics
            mongo_stats = self.storage.db.command("dbstats")
            
            # ChromaDB metrics
            chroma_count = self.vector_store.count()
            
            return {
                "mongodb": {
                    "database": mongo_stats.get("db"),
                    "collections": mongo_stats.get("collections"),
                    "data_size_mb": mongo_stats.get("dataSize", 0) / (1024**2),
                    "storage_size_mb": mongo_stats.get("storageSize", 0) / (1024**2),
                    "indexes": mongo_stats.get("indexes"),
                    "index_size_mb": mongo_stats.get("indexSize", 0) / (1024**2)
                },
                "chromadb": {
                    "total_embeddings": chroma_count,
                    "collection": "nba_stats_embeddings"
                }
            }
        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            return {}
    
    def get_recent_metrics(self, name: str = None, minutes: int = 60) -> List[Dict]:
        """
        Get recent metrics
        
        Args:
            name: Filter by metric name (optional)
            minutes: Look back this many minutes
            
        Returns:
            List of metric dictionaries
        """
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        
        filtered = [
            m.to_dict() for m in self.metrics
            if m.timestamp >= cutoff and (name is None or m.name == name)
        ]
        
        return filtered
    
    def get_metric_summary(self, name: str, minutes: int = 60) -> Dict[str, float]:
        """Get statistical summary of a metric"""
        metrics = self.get_recent_metrics(name, minutes)
        
        if not metrics:
            return {}
        
        values = [m["value"] for m in metrics]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1] if values else None
        }
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive system report"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_hours": (datetime.utcnow() - self.start_time).total_seconds() / 3600,
            "scraping": self.get_scraping_metrics(),
            "system": self.get_system_metrics(),
            "database": self.get_database_metrics(),
            "health_status": self.get_health_status()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Determine overall system health"""
        try:
            system = self.get_system_metrics()
            scraping = self.get_scraping_metrics()
            
            # Health checks
            checks = {
                "cpu_healthy": system.get("cpu", {}).get("percent", 100) < 80,
                "memory_healthy": system.get("memory", {}).get("percent", 100) < 85,
                "disk_healthy": system.get("disk", {}).get("percent", 100) < 90,
                "scraping_active": scraping.get("total_scraped", 0) > 0,
                "processing_active": scraping.get("total_processed", 0) > 0
            }
            
            overall_healthy = all(checks.values())
            
            return {
                "status": "healthy" if overall_healthy else "degraded",
                "checks": checks,
                "issues": [k for k, v in checks.items() if not v]
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def export_metrics(self, filepath: str):
        """Export metrics to JSON file"""
        try:
            metrics_data = {
                "exported_at": datetime.utcnow().isoformat(),
                "metrics": [m.to_dict() for m in self.metrics],
                "summary": self.get_comprehensive_report()
            }
            
            with open(filepath, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            logger.info(f"Metrics exported to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")


# Singleton instance
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """Get singleton metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def test_metrics():
    """Test metrics collection"""
    collector = get_metrics_collector()
    
    print("System Metrics Report")
    print("=" * 70)
    
    # Record some test metrics
    collector.record_metric("test_latency", 0.123, {"endpoint": "/api/v1/query"})
    collector.record_metric("test_throughput", 45.6, {"worker": "scraper-1"})
    
    # Get comprehensive report
    report = collector.get_comprehensive_report()
    
    print("\n1. Scraping Metrics:")
    print(json.dumps(report["scraping"], indent=2))
    
    print("\n2. System Resources:")
    print(json.dumps(report["system"], indent=2))
    
    print("\n3. Database Metrics:")
    print(json.dumps(report["database"], indent=2))
    
    print("\n4. Health Status:")
    print(json.dumps(report["health_status"], indent=2))
    
    # Export to file
    collector.export_metrics("/tmp/nba_metrics.json")
    print("\n✓ Metrics exported to /tmp/nba_metrics.json")


if __name__ == "__main__":
    test_metrics()
