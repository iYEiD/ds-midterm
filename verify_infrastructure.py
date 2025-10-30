#!/usr/bin/env python3
"""
Infrastructure Verification Script
Tests connections to MongoDB, Kafka, and Ray
"""

import sys
from pymongo import MongoClient
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient
import requests

def test_mongodb():
    """Test MongoDB connection"""
    print("🔍 Testing MongoDB connection...")
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        db = client['nba_scraper']
        collections = db.list_collection_names()
        print(f"✅ MongoDB connected successfully!")
        print(f"   Collections: {', '.join(collections)}")
        
        # Verify indexes
        for coll_name in collections:
            indexes = db[coll_name].list_indexes()
            index_names = [idx['name'] for idx in indexes]
            print(f"   {coll_name} indexes: {', '.join(index_names)}")
        
        client.close()
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

def test_kafka():
    """Test Kafka connection"""
    print("\n🔍 Testing Kafka connection...")
    try:
        admin = KafkaAdminClient(
            bootstrap_servers='localhost:9092',
            request_timeout_ms=5000
        )
        topics = admin.list_topics()
        print(f"✅ Kafka connected successfully!")
        print(f"   Topics: {', '.join(topics)}")
        
        # Check specific topics
        required_topics = ['scraping-tasks', 'scraping-results', 'processing-tasks']
        missing_topics = [t for t in required_topics if t not in topics]
        if missing_topics:
            print(f"⚠️  Missing topics: {', '.join(missing_topics)}")
        
        admin.close()
        return True
    except Exception as e:
        print(f"❌ Kafka connection failed: {e}")
        return False

def test_ray():
    """Test Ray dashboard"""
    print("\n🔍 Testing Ray dashboard...")
    try:
        response = requests.get('http://localhost:8265/api/cluster_status', timeout=5)
        if response.status_code == 200:
            print(f"✅ Ray dashboard accessible!")
            print(f"   Dashboard URL: http://localhost:8265")
            return True
        else:
            print(f"⚠️  Ray dashboard returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ray dashboard not accessible: {e}")
        return False

def main():
    print("=" * 60)
    print("Infrastructure Verification")
    print("=" * 60)
    
    results = {
        'MongoDB': test_mongodb(),
        'Kafka': test_kafka(),
        'Ray': test_ray()
    }
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    for service, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service}: {'PASS' if status else 'FAIL'}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All infrastructure services are running correctly!")
        print("✅ Phase 2 Complete - Ready to proceed to Phase 3")
        return 0
    else:
        print("\n⚠️  Some services failed. Please check the logs above.")
        print("Run 'docker-compose logs <service-name>' for more details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
