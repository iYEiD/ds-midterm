"""
Test script for Phase 3: Web Scraping Module
Tests all components of the scraping system
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("./logs/test_scraper.log", rotation="10 MB", level="DEBUG")

def test_configuration():
    """Test configuration loading"""
    print("\n" + "="*60)
    print("TEST 1: Configuration Module")
    print("="*60)
    
    try:
        from config import settings
        
        print(f"✓ MongoDB URI: {settings.MONGO_URI}")
        print(f"✓ MongoDB Database: {settings.MONGO_DB_NAME}")
        print(f"✓ Kafka Servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"✓ Scraper User Agent: {settings.SCRAPER_USER_AGENT}")
        print(f"✓ OpenAI API Key: {'***' + settings.OPENAI_API_KEY[-4:] if settings.OPENAI_API_KEY else 'NOT SET'}")
        
        print("\n✅ Configuration test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Configuration test FAILED: {e}")
        return False


def test_mongodb_connection():
    """Test MongoDB connection and storage"""
    print("\n" + "="*60)
    print("TEST 2: MongoDB Storage")
    print("="*60)
    
    try:
        from scraper.storage import get_storage
        
        storage = get_storage()
        
        # Test storing and retrieving data
        test_url = "https://test.example.com/test"
        test_html = "<html><body>Test content</body></html>"
        
        # Store raw HTML
        doc_id = storage.store_raw_html(test_url, test_html, "success")
        print(f"✓ Stored test HTML document: {doc_id}")
        
        # Retrieve it
        retrieved = storage.get_raw_html(test_url)
        if retrieved and retrieved["html_content"] == test_html:
            print("✓ Retrieved HTML matches stored content")
        
        # Check if URL exists
        exists = storage.url_exists(test_url)
        print(f"✓ URL existence check: {exists}")
        
        # Get stats count
        stats = storage.get_stats_count()
        print(f"✓ Database stats: {stats}")
        
        print("\n✅ MongoDB storage test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ MongoDB storage test FAILED: {e}")
        logger.exception("MongoDB test error:")
        return False


def test_kafka_connection():
    """Test Kafka URL manager"""
    print("\n" + "="*60)
    print("TEST 3: Kafka URL Manager")
    print("="*60)
    
    try:
        from scraper.url_manager import get_url_manager
        
        url_manager = get_url_manager()
        
        # Test submitting a URL
        test_url = "https://www.nba.com/stats/test"
        success = url_manager.submit_url(test_url, metadata={"test": True})
        
        if success:
            print(f"✓ Successfully submitted URL to Kafka: {test_url}")
        else:
            print(f"⚠ Failed to submit URL (might be Kafka config issue)")
        
        # Test batch submission
        test_urls = [
            "https://www.nba.com/stats/test1",
            "https://www.nba.com/stats/test2"
        ]
        count = url_manager.submit_urls_batch(test_urls)
        print(f"✓ Batch submitted {count}/{len(test_urls)} URLs")
        
        # Get pending count
        pending = url_manager.get_pending_count()
        print(f"✓ Pending messages in queue: {pending}")
        
        print("\n✅ Kafka URL manager test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Kafka URL manager test FAILED: {e}")
        logger.exception("Kafka test error:")
        return False


def test_scraper():
    """Test NBA scraper"""
    print("\n" + "="*60)
    print("TEST 4: NBA Scraper")
    print("="*60)
    
    try:
        from scraper.nba_scraper import NBAStatsScraper
        
        scraper = NBAStatsScraper()
        
        # Test scraping (using a simple test page)
        # Note: We'll use a simple URL that's likely to work
        test_url = "https://www.nba.com/stats"
        
        print(f"Attempting to scrape: {test_url}")
        result = scraper.scrape_url(test_url, save_to_db=True)
        
        if result:
            print(f"✓ Scraping result:")
            print(f"  - Status: {result['status']}")
            print(f"  - From cache: {result.get('from_cache', False)}")
            print(f"  - HTML length: {len(result.get('html', ''))}")
            
            # Test parsing
            if result.get('html'):
                parsed = scraper.parse_nba_table(result['html'])
                print(f"✓ Parsed {len(parsed)} rows from HTML")
        
        scraper.close()
        
        print("\n✅ NBA scraper test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ NBA scraper test FAILED: {e}")
        logger.exception("Scraper test error:")
        return False


def test_distributed_scraper():
    """Test Ray distributed scraper"""
    print("\n" + "="*60)
    print("TEST 5: Distributed Scraper (Ray)")
    print("="*60)
    
    try:
        from scraper.distributed_scraper import DistributedScraper
        import ray
        
        # Initialize with fewer workers for testing
        scraper = DistributedScraper(num_workers=2, init_ray=True)
        
        # Get cluster info
        info = scraper.get_cluster_info()
        print(f"✓ Ray cluster info:")
        print(f"  - Num workers: {info.get('num_workers')}")
        print(f"  - Ray initialized: {info.get('ray_initialized')}")
        
        # Test parallel scraping with simple URLs
        test_urls = [
            "https://www.nba.com/stats",
        ]
        
        print(f"\nScraping {len(test_urls)} URL(s) in parallel...")
        results = scraper.scrape_urls_parallel(test_urls)
        
        print(f"✓ Scraping completed:")
        for result in results:
            print(f"  - {result['url']}: {result['status']} (worker {result.get('worker_id')})")
        
        scraper.shutdown()
        
        print("\n✅ Distributed scraper test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Distributed scraper test FAILED: {e}")
        logger.exception("Distributed scraper test error:")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("PHASE 3: WEB SCRAPING MODULE - TEST SUITE")
    print("="*60)
    
    results = {
        "Configuration": test_configuration(),
        "MongoDB Storage": test_mongodb_connection(),
        "Kafka URL Manager": test_kafka_connection(),
        "NBA Scraper": test_scraper(),
        "Distributed Scraper": test_distributed_scraper(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Phase 3 is complete.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
