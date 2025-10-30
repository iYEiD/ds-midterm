# 🧪 Distributed System Testing Guide

This guide explains how to test the **fully distributed Kafka-based scraping system**.

## Architecture Overview

```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│ Orchestrator │────▶│ Kafka Queue   │────▶│  Scraper     │
│   (Submit)   │     │ (scraping-    │     │  Workers     │
└──────────────┘     │   tasks)      │     │  (2+)        │
                     └───────────────┘     └──────┬───────┘
                                                   │
                                                   ▼
                     ┌───────────────┐     ┌──────────────┐
                     │ Kafka Queue   │◀────│  MongoDB     │
                     │ (scraping-    │     │  (Raw Data)  │
                     │   results)    │     └──────────────┘
                     └───────┬───────┘
                             │
                             ▼
                     ┌──────────────┐
                     │  Processor   │
                     │  Workers     │
                     │  (2+)        │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  MongoDB     │     │  ChromaDB    │
                     │ (Processed)  │     │ (Embeddings) │
                     └──────────────┘     └──────────────┘
```

## Prerequisites

### 1. Verify Infrastructure is Running

```bash
cd /home/yeid/DS-MT
docker-compose ps
```

**Expected output:** All services (Zookeeper, Kafka, MongoDB, Ray) should be **Up**.

If not running:
```bash
docker-compose up -d
```

### 2. Verify Kafka Topics Exist

```bash
# Check topics
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
```

**Expected output:**
- `scraping-tasks`
- `scraping-results`
- `processing-tasks`

If topics don't exist, they'll be auto-created on first use.

### 3. Activate Virtual Environment

```bash
source venv/bin/activate
```

## Testing Approaches

### Level 1: Unit Testing (Components in Isolation)

#### Test Kafka URL Manager
```bash
python -c "
from scraper.url_manager import get_url_manager
url_mgr = get_url_manager()
success = url_mgr.submit_url('https://test.com', {'test': True})
print(f'Kafka submit: {success}')
print(f'Pending count: {url_mgr.get_pending_count()}')
"
```

**Expected:** `Kafka submit: True`, `Pending count: 1+`

---

### Level 2: Worker Testing (Individual Workers)

#### Test Scraper Worker (Manual Mode)

**Terminal 1 - Start Worker:**
```bash
python scraper/kafka_scraper_worker.py --worker-id test-scraper-1
```

**Terminal 2 - Submit URL:**
```bash
python -c "
from scraper.url_manager import get_url_manager
url_mgr = get_url_manager()
url_mgr.submit_url(
    'https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=BLK',
    {'test': True}
)
print('URL submitted to Kafka')
"
```

**Watch Terminal 1** - You should see:
- Worker receives task
- Scrapy starts scraping
- Data stored in MongoDB
- Result sent back to Kafka

**Verify in MongoDB:**
```bash
python -c "
from scraper.storage import get_storage
s = get_storage()
print(f'Raw docs: {s.get_stats_count()}')
"
```

---

#### Test Processor Worker (Manual Mode)

**Terminal 1 - Start Processor:**
```bash
python processor/kafka_processor_worker.py --worker-id test-processor-1
```

The processor should automatically pick up results from the scraper and:
- Parse the data
- Normalize stats
- Generate embeddings
- Store in ChromaDB

**Verify in ChromaDB:**
```bash
python -c "
from rag.vector_store import get_vector_store
vs = get_vector_store()
print(f'Embeddings: {vs.count()}')
"
```

---

### Level 3: Orchestrated Testing (Full Pipeline)

#### Option A: Quick Test with Orchestrator

```bash
python orchestrator.py --test
```

This runs a predefined test with 3 NBA stats URLs (PTS, REB, AST leaders).

**What happens:**
1. Orchestrator submits 3 URLs to Kafka
2. Monitors progress
3. Reports stats

**Note:** Workers must be running separately!

---

#### Option B: Custom URLs

Create a file `test_urls.txt`:
```
https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=PTS
https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=AST
```

Run:
```bash
python orchestrator.py --url-file test_urls.txt --monitor --timeout 180
```

---

### Level 4: Full E2E Automated Test

This test **automatically starts workers**, runs the pipeline, and verifies results.

```bash
python tests/test_distributed_e2e.py
```

**What it does:**
1. Gets baseline stats (MongoDB, ChromaDB)
2. Starts 2 scraper workers + 2 processor workers
3. Submits test URL via orchestrator
4. Monitors for completion
5. Verifies new data was created
6. Stops all workers
7. Exits with success/failure code

**Expected output:**
```
============================================================
DISTRIBUTED SYSTEM E2E TEST
============================================================
[INFO] Initial stats: MongoDB={...}, ChromaDB=...
[INFO] Starting 2 scraper workers and 2 processor workers...
[INFO] Started scraper worker: scraper-1 (PID: 12345)
[INFO] Started scraper worker: scraper-2 (PID: 12346)
[INFO] Started processor worker: processor-1 (PID: 12347)
[INFO] Started processor worker: processor-2 (PID: 12348)
[INFO] Submitting 1 URLs...
[INFO] Job result: success
[INFO] Verifying results...
[INFO]   New raw documents: 1 (expected >= 1)
[INFO]   New processed stats: 50
[INFO]   New embeddings: 50

============================================================
TEST RESULTS
============================================================
Status: ✓ PASSED
New raw documents: 1
New processed stats: 50
New embeddings: 50
============================================================
```

---

## Production-Style Testing (Multiple Workers)

### Step 1: Start Multiple Scraper Workers

```bash
# Terminal 1
python scraper/kafka_scraper_worker.py --worker-id scraper-1

# Terminal 2
python scraper/kafka_scraper_worker.py --worker-id scraper-2

# Terminal 3
python scraper/kafka_scraper_worker.py --worker-id scraper-3
```

### Step 2: Start Multiple Processor Workers

```bash
# Terminal 4
python processor/kafka_processor_worker.py --worker-id processor-1

# Terminal 5
python processor/kafka_processor_worker.py --worker-id processor-2
```

### Step 3: Submit Batch Job

```bash
# Terminal 6
python orchestrator.py --urls \
  "https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=PTS" \
  "https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=REB" \
  "https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=AST" \
  "https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=STL" \
  "https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=BLK" \
  --monitor --timeout 300
```

**What you'll see:**
- Each scraper worker picks up URLs (round-robin via Kafka consumer group)
- Workers process in parallel
- Results flow through Kafka to processor workers
- Processors work in parallel on embeddings
- Orchestrator shows progress

---

## Monitoring & Debugging

### Monitor Kafka Topics

**Check pending tasks:**
```bash
python -c "
from scraper.url_manager import get_url_manager
print(f'Pending scraping tasks: {get_url_manager().get_pending_count()}')
"
```

**Check results queue:**
```bash
docker exec -it kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group processor-workers
```

### Monitor MongoDB

```bash
python -c "
from scraper.storage import get_storage
stats = get_storage().get_stats_count()
print(f'Raw: {stats[\"raw_data_count\"]}')
print(f'Processed: {stats[\"processed_stats_count\"]}')
print(f'Unique players: {stats[\"unique_players\"]}')
"
```

### Monitor ChromaDB

```bash
python -c "
from rag.vector_store import get_vector_store
print(f'Total embeddings: {get_vector_store().count()}')
"
```

### Check Worker Health

```bash
# See worker logs
ps aux | grep kafka_scraper_worker
ps aux | grep kafka_processor_worker
```

---

## Fault Tolerance Testing

### Test 1: Kill a Scraper Worker

1. Start 3 scraper workers
2. Submit 10 URLs
3. While processing, kill one worker: `kill -9 <PID>`
4. **Expected:** Other workers pick up the slack, no data loss

### Test 2: Kill a Processor Worker

1. Start 2 processor workers
2. Let them process
3. Kill one: `kill -9 <PID>`
4. **Expected:** Remaining worker continues, Kafka retries failed messages

### Test 3: Restart Kafka

```bash
docker-compose restart kafka
```

**Expected:** Workers reconnect automatically, messages persisted

---

## Performance Testing

### Measure Throughput

```bash
time python orchestrator.py --urls \
  $(cat urls_100.txt) \
  --monitor --timeout 600
```

**Metrics to track:**
- URLs/minute
- Players processed/minute
- Embeddings generated/minute

---

## Troubleshooting

### Issue: Workers not consuming

**Check:**
```bash
# Kafka consumer lag
docker exec -it kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --all-groups
```

### Issue: No data in MongoDB

**Check:**
- Scraper worker logs for errors
- Kafka connectivity
- MongoDB connectivity

### Issue: No embeddings in ChromaDB

**Check:**
- Processor worker logs
- OpenAI API key validity
- OpenAI API rate limits

---

## Success Criteria

✅ **System is working correctly if:**

1. **Kafka Integration:** URLs submitted via orchestrator appear in worker logs
2. **Parallel Processing:** Multiple workers process different URLs simultaneously  
3. **Data Flow:** Raw data → MongoDB → Processor → Embeddings → ChromaDB
4. **Fault Tolerance:** Killing a worker doesn't stop the system
5. **No Data Loss:** All submitted URLs eventually get processed
6. **E2E Test:** `test_distributed_e2e.py` passes

---

## Next Steps After Successful Testing

1. ✅ Document your results with screenshots
2. ✅ Commit the distributed architecture
3. ✅ Move to Phase 6: FastAPI Service (expose distributed system via REST API)
4. ✅ Consider adding Ray for advanced distributed processing (optional)

---

## Quick Reference Commands

```bash
# Start all infrastructure
docker-compose up -d

# Run E2E test
python tests/test_distributed_e2e.py

# Start workers manually
python scraper/kafka_scraper_worker.py --worker-id worker-1
python processor/kafka_processor_worker.py --worker-id proc-1

# Submit test job
python orchestrator.py --test

# Check system status
python -c "from scraper.storage import get_storage; from rag.vector_store import get_vector_store; print(f'MongoDB: {get_storage().get_stats_count()}'); print(f'ChromaDB: {get_vector_store().count()}')"
```
