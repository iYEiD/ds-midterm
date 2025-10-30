# Distributed RAG-Based Web Scraper Framework - Project Plan

## Target Use Case
Scraping NBA player statistics tables from `https://www.nba.com/stats/alltime-leaders` and similar structured data pages.

## Tech Stack
- **Distributed Computing**: Ray
- **Message Queue**: Kafka
- **Databases**: MongoDB (raw data), ChromaDB (vectors)
- **LLM**: OpenAI API
- **Framework**: Scrapy, FastAPI
- **Deployment**: Docker Compose → Kubernetes (later phase)

---

## PHASE 1: Environment & Repository Setup

### 1.1 Initialize Project Structure
```
distributed-rag-scraper/
├── scraper/              # Web scraping module
├── processor/            # Data processing module
├── rag/                  # RAG and LLM integration
├── api/                  # FastAPI service
├── infrastructure/       # Kafka, MongoDB configs
├── monitoring/           # Prometheus, Grafana (later)
├── docker/               # Dockerfiles
├── tests/                # Unit and integration tests
├── docs/                 # Documentation and screenshots
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### 1.2 Setup Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

### 1.3 Initialize Git Repository
```bash
git init
git remote add origin <your-repo-url>
# Create .gitignore for Python, Docker, env files
```

### 1.4 Install Core Dependencies
Create `requirements.txt` with:
- scrapy
- beautifulsoup4, lxml
- ray[default]
- kafka-python
- pymongo
- chromadb
- openai
- fastapi, uvicorn
- pydantic
- python-dotenv
- requests

**Checkpoint**: Virtual environment active, dependencies installed, repo initialized

---

## PHASE 2: Local Infrastructure with Docker Compose

### 2.1 Create docker-compose.yml
Set up containers for:
- **Zookeeper** (Kafka dependency)
- **Kafka** (message broker)
- **MongoDB** (raw data storage)
- **Ray Head Node** (coordinator)

### 2.2 Configure Services
- MongoDB: Port 27017, volume mount for persistence
- Kafka: Port 9092, configure topics: `scraping-tasks`, `scraping-results`
- Ray: Port 8265 (dashboard), 6379 (Redis)
- Network: Create shared network `scraper-network`

### 2.3 Create .env File
```
MONGO_URI=mongodb://localhost:27017/
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
OPENAI_API_KEY=your_api_key_here
RAY_ADDRESS=ray://localhost:10001
CHROMA_PERSIST_DIR=./chroma_data
```

### 2.4 Test Infrastructure
```bash
docker-compose up -d
# Verify all services running
docker-compose ps
```

**Checkpoint**: All infrastructure containers running, accessible locally
**Screenshot**: Docker containers running, Ray dashboard, MongoDB connection

---

## PHASE 3: Web Scraping Module Development

### 3.1 Create Scrapy Spider for NBA Stats
File: `scraper/nba_spider.py`
- Target: NBA stats tables (alltime-leaders, player stats)
- Extract: Table headers and rows
- Handle pagination and dynamic season/category filters
- Parse JavaScript-rendered content (use Playwright/Selenium if needed)

### 3.2 Implement URL Manager with Kafka
File: `scraper/url_manager.py`
- Producer: Push URLs to `scraping-tasks` topic
- Consumer: Workers pull URLs to scrape
- Handle URL deduplication (check MongoDB before adding)

### 3.3 Distributed Scraping with Ray
File: `scraper/distributed_scraper.py`
- Initialize Ray cluster (connect to head node)
- Create Ray remote functions for parallel scraping
- Distribute URLs across Ray workers
- Implement retry logic for failed requests

### 3.4 Store Raw Data in MongoDB
File: `scraper/storage.py`
- Collections: `raw_scraped_data`, `scraping_metadata`
- Schema: `{url, timestamp, html_content, status, metadata}`
- Create indexes on URL and timestamp

### 3.5 Test Scraping Module
```bash
# Test single URL scraping
python scraper/test_scraper.py
# Test distributed scraping (5-10 URLs)
python scraper/test_distributed.py
```

**Checkpoint**: Successfully scrape NBA stats tables, store in MongoDB
**Screenshot**: MongoDB data, Ray dashboard showing tasks, Scrapy logs

---

## PHASE 4: Data Processing Module

### 4.1 HTML Parser for NBA Tables
File: `processor/html_parser.py`
- Extract table headers (PLAYER, GP, MIN, PTS, etc.)
- Parse table rows into structured data
- Handle different table formats (seasonal vs career stats)
- Clean special characters, handle missing values

### 4.2 Data Normalization
File: `processor/normalizer.py`
- Convert to JSON structure:
```json
{
  "player_name": "LeBron James",
  "stats": {
    "GP": 1421, "MIN": 54637, "PTS": 40474,
    "FGM": 14934, "FGA": 30813, "FG%": 0.505,
    ...
  },
  "metadata": {
    "season_type": "Regular Season",
    "scraped_at": "2025-01-15T10:30:00Z"
  }
}
```

### 4.3 MongoDB Storage for Clean Data
- Collection: `processed_stats`
- Indexes: player_name, season_type, scraped_at
- Aggregation pipeline for stats calculations

### 4.4 Ray-Based Distributed Processing
File: `processor/distributed_processor.py`
- Ray actors to process batches of raw HTML
- Parallel processing pipeline: fetch raw → parse → normalize → store
- Error handling and logging

### 4.5 Test Processing Pipeline
```bash
# Process sample of scraped data
python processor/test_processor.py
# Verify data quality in MongoDB
```

**Checkpoint**: Raw HTML converted to clean JSON in MongoDB
**Screenshot**: MongoDB clean data, processing logs, data sample

---

## PHASE 5: RAG Integration with ChromaDB and OpenAI

### 5.1 Setup ChromaDB
File: `rag/vector_store.py`
- Initialize persistent ChromaDB client
- Create collection: `nba_stats_embeddings`
- Configure embedding function (OpenAI text-embedding-3-small)

### 5.2 Text Chunking and Embedding
File: `rag/embedder.py`
- Convert player stats to descriptive text:
  - "LeBron James played 1421 games with 40474 total points..."
- Generate embeddings using OpenAI API
- Store in ChromaDB with metadata (player_name, stat_category)

### 5.3 Retrieval Function
File: `rag/retriever.py`
- Query ChromaDB with natural language:
  - "Who are the top scorers in NBA history?"
- Return top-k relevant player stats
- Include similarity scores

### 5.4 LLM Augmentation
File: `rag/llm_augmenter.py`
- Combine retrieved stats with OpenAI GPT-4
- Generate contextual summaries:
  - Compare players across eras
  - Provide insights on statistical trends
  - Answer complex queries
- Implement prompt templates

### 5.5 Test RAG Pipeline
```bash
# Test embedding generation
python rag/test_embeddings.py
# Test retrieval
python rag/test_retrieval.py
# Test end-to-end RAG query
python rag/test_rag.py "Who is the all-time steals leader?"
```

**Checkpoint**: RAG system returns relevant stats + AI-generated insights
**Screenshot**: ChromaDB data, sample queries and responses, OpenAI API logs

---

## PHASE 6: FastAPI Service Development

### 6.1 Create API Structure
File: `api/main.py`
- FastAPI app initialization
- CORS middleware
- API versioning (/api/v1)

### 6.2 Implement Endpoints

**Raw Data Endpoints**
- `GET /api/v1/raw/{url_id}` - Fetch raw scraped HTML
- `GET /api/v1/raw/list` - List all scraped URLs with pagination

**Processed Data Endpoints**
- `GET /api/v1/stats/player/{name}` - Get player stats
- `GET /api/v1/stats/leaders?category={PTS|STL|AST}` - Top players by stat
- `GET /api/v1/stats/search?query={text}` - Search processed data

**RAG Query Endpoints**
- `POST /api/v1/query` - Natural language query with RAG
  ```json
  {
    "query": "Compare LeBron and Jordan in playoffs",
    "top_k": 5
  }
  ```
- `GET /api/v1/query/history` - Query history

**System Endpoints**
- `GET /api/v1/health` - Health check
- `GET /api/v1/stats/system` - Scraping statistics

### 6.3 Authentication & Rate Limiting
File: `api/auth.py`
- API key-based authentication
- Rate limiting: 100 requests/hour per key
- Use slowapi for rate limiting

### 6.4 Test API
```bash
# Start API server
uvicorn api.main:app --reload
# Test endpoints with curl/Postman
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/stats/leaders?category=PTS
```

**Checkpoint**: All API endpoints functional and tested
**Screenshot**: API documentation (FastAPI /docs), sample requests/responses

---

## PHASE 7: Load Balancing & Fault Tolerance

### 7.1 Configure Nginx Load Balancer
File: `infrastructure/nginx.conf`
- Distribute requests across multiple API instances
- Health checks
- Upstream configuration

### 7.2 Kafka Consumer Groups
File: `scraper/consumer_group.py`
- Multiple scraper workers in same consumer group
- Automatic rebalancing on worker failure
- Offset management

### 7.3 Ray Fault Tolerance
File: `scraper/fault_tolerant_scraper.py`
- Configure Ray actor lifetimes
- Implement task retry with exponential backoff
- Dead letter queue for failed tasks

### 7.4 Monitoring Setup (Basic)
- Add logging to all modules
- Track metrics: scraping rate, processing time, API latency
- Store logs in structured format

### 7.5 Test Fault Tolerance
```bash
# Kill a scraper worker during operation
# Verify tasks are redistributed
# Kill Ray worker, verify auto-restart
```

**Checkpoint**: System handles failures gracefully
**Screenshot**: Load balancing in action, failure recovery logs

---

## PHASE 8: Integration Testing & Documentation

### 8.1 End-to-End Integration Test
File: `tests/test_e2e.py`
- Start all services
- Submit URLs → Scrape → Process → Embed → Query via API
- Verify data flow through entire pipeline

### 8.2 Performance Testing
- Test with 100+ NBA stat pages
- Measure throughput (pages/minute)
- Monitor resource usage

### 8.3 Create Flowchart
Tools: draw.io, Lucidchart, or Mermaid
- Show data flow from URL submission to API response
- Include all components: Kafka, Ray, MongoDB, ChromaDB, OpenAI

### 8.4 Documentation with Screenshots
Structure: `docs/report.md`
1. **Phase 1-2**: Environment setup screenshots
2. **Phase 3**: Scraping in action (Ray dashboard, MongoDB data)
3. **Phase 4**: Data processing (before/after comparison)
4. **Phase 5**: RAG system (embeddings, queries, responses)
5. **Phase 6**: API testing (Postman/curl screenshots)
6. **Phase 7**: Load balancing and fault tolerance
7. **Flowchart**: Complete system architecture

**Checkpoint**: Complete documentation ready for submission

---

## PHASE 9: Monitoring with Prometheus & Grafana (Secondary)

### 9.1 Setup Prometheus
- Add Prometheus container to docker-compose
- Configure scrape targets: API, Ray, Kafka exporters
- Define custom metrics

### 9.2 Setup Grafana
- Add Grafana container
- Create dashboards:
  - Scraping metrics (URLs/min, success rate)
  - Processing metrics (processing time, queue depth)
  - API metrics (requests/sec, latency)
  - System resources (CPU, memory, disk)

### 9.3 Alerting Rules
- Alert on scraping failures
- Alert on API downtime
- Alert on resource exhaustion

**Checkpoint**: Real-time monitoring operational
**Screenshot**: Grafana dashboards

---

## PHASE 10: Cloud Deployment (Secondary)

### 10.1 Dockerize All Services
Create Dockerfiles for:
- `docker/scraper.Dockerfile`
- `docker/processor.Dockerfile`
- `docker/api.Dockerfile`
- `docker/rag.Dockerfile`

### 10.2 Test Docker Compose Locally
```bash
docker-compose -f docker-compose.prod.yml up
# Test entire system in containerized environment
```

### 10.3 Kubernetes Configuration (Later Decision)
Files: `k8s/`
- Deployments for each service
- StatefulSets for MongoDB, Kafka
- Services and Ingress
- ConfigMaps and Secrets
- HorizontalPodAutoscaler for scraper workers

### 10.4 Deploy to Cloud
**Decision Point**: Choose cloud provider (AWS/GCP/Azure)
- Setup managed Kubernetes cluster
- Configure persistent volumes
- Deploy application
- Configure auto-scaling

**Checkpoint**: System running in cloud environment

---

## PHASE 11: Web UI (Final Phase)

### 11.1 Setup React/Vue.js Project
```bash
cd ui
npm create vite@latest . -- --template react
npm install axios recharts
```

### 11.2 Create UI Components
- Search interface for player stats
- Natural language query box (RAG integration)
- Data visualization (charts for stats comparison)
- Scraping job manager (submit URLs, view status)

### 11.3 Integrate Elasticsearch (Optional)
- Add Elasticsearch to docker-compose
- Index processed data for fast search
- Connect UI search to Elasticsearch

### 11.4 Connect to FastAPI Backend
- API client wrapper
- Real-time updates with WebSockets
- Error handling and loading states

**Checkpoint**: Functional web interface for the system
**Screenshot**: UI screenshots of all features

---

## Testing Strategy

### Unit Tests
- Test each module independently
- Mock external dependencies (Kafka, MongoDB, OpenAI)
- Coverage target: 70%+

### Integration Tests
- Test component interactions
- Use test containers for databases
- Test Kafka message flow

### Load Tests
- Use locust or k6
- Test API under load
- Test distributed scraping with 1000+ URLs

---

## Deliverables Checklist

- [ ] Complete codebase in Git repository
- [ ] `docker-compose.yml` for local deployment
- [ ] Comprehensive `README.md` with setup instructions
- [ ] `docs/report.md` with phase-by-phase screenshots and explanations
- [ ] Flowchart diagram (PNG/PDF)
- [ ] `requirements.txt` and all config files
- [ ] Test suite with passing tests
- [ ] API documentation (FastAPI auto-generated)
- [ ] Demo video or instructions for testing

---

## Development Tips

1. **Incremental Development**: Complete and test each phase before moving forward
2. **Frequent Commits**: Commit after each working feature
3. **Screenshot Everything**: Take screenshots immediately after completing each phase
4. **Test Early**: Don't accumulate untested code
5. **Monitor Resources**: Watch Docker container resources
6. **API Keys**: Never commit `.env` file to Git
7. **Documentation**: Write explanations while implementing, not after

---

## Troubleshooting Guide

### Kafka Connection Issues
- Verify Zookeeper is running
- Check Kafka broker logs
- Ensure topics are created

### Ray Connection Issues
- Check Ray dashboard (localhost:8265)
- Verify Ray head node is running
- Check firewall rules

### MongoDB Issues
- Verify connection string
- Check disk space
- Review indexes for performance

### OpenAI API Issues
- Check API key validity
- Monitor rate limits
- Implement exponential backoff

### ChromaDB Issues
- Ensure persist directory exists
- Check disk space
- Verify embedding dimensions match

---

## Next Steps After Core Implementation

1. Review this plan and adjust based on your needs
2. Set up Phase 1 (environment)
3. Get Phase 2 (Docker infrastructure) running
4. Begin Phase 3 (scraping) with a single NBA stats page
5. Expand incrementally

**Good luck! 🚀**