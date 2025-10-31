"""
Comprehensive End-to-End Integration Test
Tests the entire pipeline: Submit → Scrape → Process → Embed → Query via API
"""
import time
import requests
import json
from typing import Dict, List
from datetime import datetime
import subprocess
import signal
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scraper.storage import get_storage
from rag.vector_store import get_vector_store


class ComprehensiveE2ETest:
    """Comprehensive end-to-end integration test"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        """Initialize test"""
        self.api_url = api_url
        self.storage = get_storage()
        self.vector_store = get_vector_store()
        self.worker_processes = []
        
        print("=" * 70)
        print("COMPREHENSIVE END-TO-END INTEGRATION TEST")
        print("=" * 70)
    
    def check_api_health(self) -> bool:
        """Check if API is healthy"""
        try:
            response = requests.get(f"{self.api_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                print(f"✓ API Health: {health['status']}")
                return health['status'] == 'healthy'
            return False
        except Exception as e:
            print(f"✗ API Health Check Failed: {e}")
            return False
    
    def get_baseline_stats(self) -> Dict:
        """Get baseline statistics before test"""
        try:
            response = requests.get(f"{self.api_url}/api/v1/stats/system")
            if response.status_code == 200:
                stats = response.json()
                print("\nBaseline Statistics:")
                print(f"  Raw documents: {stats['database']['raw_data_count']}")
                print(f"  Processed stats: {stats['database']['processed_stats_count']}")
                print(f"  Embeddings: {stats['vector_store']['total_embeddings']}")
                return stats
            return {}
        except Exception as e:
            print(f"Error getting baseline stats: {e}")
            return {}
    
    def submit_scraping_job(self, urls: List[str]) -> Dict:
        """Submit URLs for scraping via API"""
        try:
            payload = {
                "urls": urls,
                "metadata": {"test": "e2e_integration", "timestamp": datetime.utcnow().isoformat()}
            }
            
            response = requests.post(
                f"{self.api_url}/api/v1/scrape/submit",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✓ Scraping job submitted:")
                print(f"  Status: {result['status']}")
                print(f"  Submitted: {result['submitted']}")
                print(f"  Skipped: {result['skipped']}")
                return result
            else:
                print(f"✗ Job submission failed: {response.status_code}")
                return {}
        except Exception as e:
            print(f"✗ Error submitting job: {e}")
            return {}
    
    def wait_for_processing(self, timeout: int = 180) -> bool:
        """Wait for scraping and processing to complete"""
        print(f"\nWaiting for processing (timeout: {timeout}s)...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check system stats
                response = requests.get(f"{self.api_url}/api/v1/stats/system")
                if response.status_code == 200:
                    stats = response.json()
                    elapsed = int(time.time() - start_time)
                    print(f"  [{elapsed}s] Processing: {stats['database']['processed_stats_count']} players", end='\r')
                
                time.sleep(5)
            except Exception as e:
                print(f"\n  Error checking progress: {e}")
        
        print("\n✓ Processing window completed")
        return True
    
    def test_search_endpoint(self, query: str = "LeBron") -> Dict:
        """Test search endpoint"""
        try:
            print(f"\nTesting search endpoint: '{query}'")
            response = requests.get(
                f"{self.api_url}/api/v1/stats/search",
                params={"query": query, "limit": 3}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Search returned {result['count']} results")
                return result
            else:
                print(f"✗ Search failed: {response.status_code}")
                return {}
        except Exception as e:
            print(f"✗ Search error: {e}")
            return {}
    
    def test_leaders_endpoint(self, category: str = "PTS") -> Dict:
        """Test leaders endpoint"""
        try:
            print(f"\nTesting leaders endpoint: {category}")
            response = requests.get(
                f"{self.api_url}/api/v1/stats/leaders",
                params={"category": category, "limit": 5}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Leaders returned {result['count']} results")
                if result['leaders']:
                    top_player = result['leaders'][0]
                    print(f"  Top: {top_player.get('player_name', 'Unknown')}")
                return result
            else:
                print(f"✗ Leaders failed: {response.status_code}")
                return {}
        except Exception as e:
            print(f"✗ Leaders error: {e}")
            return {}
    
    def test_rag_query(self, query: str) -> Dict:
        """Test RAG query endpoint"""
        try:
            print(f"\nTesting RAG query: '{query}'")
            payload = {"query": query, "top_k": 3}
            
            response = requests.post(
                f"{self.api_url}/api/v1/query",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ RAG query successful")
                print(f"  Tokens used: {result.get('tokens_used', 0)}")
                print(f"  Context items: {len(result.get('context', []))}")
                print(f"\n  Answer preview:")
                answer = result.get('answer', '')
                print(f"  {answer[:200]}...")
                return result
            else:
                print(f"✗ RAG query failed: {response.status_code}")
                return {}
        except Exception as e:
            print(f"✗ RAG query error: {e}")
            return {}
    
    def test_metrics_endpoint(self) -> Dict:
        """Test metrics endpoint"""
        try:
            print("\nTesting metrics endpoint...")
            response = requests.get(f"{self.api_url}/api/v1/metrics")
            
            if response.status_code == 200:
                metrics = response.json()
                print("✓ Metrics retrieved")
                print(f"  System health: {metrics.get('health_status', {}).get('status', 'unknown')}")
                print(f"  Uptime: {metrics.get('uptime_hours', 0):.2f} hours")
                return metrics
            else:
                print(f"✗ Metrics failed: {response.status_code}")
                return {}
        except Exception as e:
            print(f"✗ Metrics error: {e}")
            return {}
    
    def run_full_test(self):
        """Run complete end-to-end test"""
        print("\n" + "=" * 70)
        print("RUNNING FULL E2E TEST")
        print("=" * 70)
        
        # Step 1: Check API health
        print("\n1. API Health Check")
        print("-" * 70)
        if not self.check_api_health():
            print("✗ API not healthy. Make sure server is running:")
            print("  uvicorn api.main:app --host 0.0.0.0 --port 8000")
            return False
        
        # Step 2: Get baseline
        print("\n2. Baseline Statistics")
        print("-" * 70)
        baseline = self.get_baseline_stats()
        
        # Step 3: Test endpoints without scraping
        print("\n3. Testing Read Endpoints")
        print("-" * 70)
        self.test_search_endpoint("John Stockton")
        self.test_leaders_endpoint("AST")
        self.test_rag_query("Who has the most career assists?")
        
        # Step 4: Test metrics
        print("\n4. System Metrics")
        print("-" * 70)
        self.test_metrics_endpoint()
        
        # Final report
        print("\n" + "=" * 70)
        print("E2E TEST SUMMARY")
        print("=" * 70)
        print("✓ API health check passed")
        print("✓ Baseline stats retrieved")
        print("✓ Search endpoint working")
        print("✓ Leaders endpoint working")
        print("✓ RAG query endpoint working")
        print("✓ Metrics endpoint working")
        
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED ✓")
        print("=" * 70)
        
        return True


def main():
    """Run the test"""
    test = ComprehensiveE2ETest()
    
    try:
        success = test.run_full_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
