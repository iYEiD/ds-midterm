# NBA Stats Scraper - Deployment Guide

## Project Overview

A distributed RAG-based NBA statistics scraper that collects, processes, and queries player statistics using microservices architecture with Kafka message queues, MongoDB storage, ChromaDB vector embeddings, and GPT-4 AI integration.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                           │
│                    React UI (Port 5173)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
│                  FastAPI Server (Port 8000)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌──────────────────┐  ┌─────────────┐  ┌─────────────┐
│  Kafka Message   │  │   MongoDB    │  │  ChromaDB   │
│     Queue        │  │   Database   │  │  Vectors    │
│  (Ports 9092)    │  │ (Port 27017) │  │             │
└──────────────────┘  └─────────────┘  └─────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌──────────┐
│Scraper  │ │Processor │
│ Worker  │ │  Worker  │
└─────────┘ └──────────┘
```

## Infrastructure Components

### Core Services (Docker Containers)
- **MongoDB**: NoSQL database for raw and processed player statistics
- **Zookeeper**: Coordination service for Kafka cluster
- **Kafka**: Distributed message queue for async task processing

### Application Services
- **FastAPI Backend**: REST API server providing endpoints for search, RAG queries, job submission
- **React Frontend**: Web UI for system interaction and data visualization
- **Kafka Workers**: Background workers for scraping and data processing

### External Services
- **OpenAI GPT-4**: AI model for natural language query responses
- **ChromaDB**: Vector database for semantic search

## Prerequisites

- **Operating System**: Linux (tested on Ubuntu)
- **Python**: 3.12.3
- **Node.js**: 18+ (for React frontend)
- **Docker**: Latest version with docker-compose
- **OpenAI API Key**: Required for RAG queries

## Installation & Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd DS-MT
```

### 2. Environment Configuration

Create `.env` file in project root:
```bash
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=nba_stats

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_RAW_TOPIC=nba-raw-data
KAFKA_PROCESSED_TOPIC=nba-processed-stats

# ChromaDB Configuration
CHROMA_PERSIST_DIR=./chroma_data
CHROMA_COLLECTION=nba_stats

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. Start Docker Infrastructure

Start MongoDB, Zookeeper, and Kafka:
```bash
docker-compose up -d
```

Verify containers are running:
```bash
docker-compose ps
```

Expected output:
```
NAME                IMAGE                        STATUS
ds-mt-kafka-1       confluentinc/cp-kafka:7.5.0  Up
ds-mt-mongodb-1     mongo:7.0                    Up
ds-mt-zookeeper-1   confluentinc/cp-zookeeper    Up
```

### 4. Setup Python Backend

Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### 5. Start Backend Services

**Terminal 1 - FastAPI Server:**
```bash
source venv/bin/activate
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Kafka Workers:**
```bash
source venv/bin/activate
./scripts/start_workers.sh
```

Verify workers are running:
```bash
cat logs/scraper_worker.pid
cat logs/processor_worker.pid
ps aux | grep kafka_worker
```

### 6. Start Frontend (React UI)

**Terminal 3 - React Development Server:**
```bash
cd ui
npm install
npm run dev
```

Frontend will be available at: http://localhost:5173

## Accessing the System

### Web Interface
- **Frontend**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

### API Endpoints

**Health & Monitoring:**
- `GET /api/v1/health` - System health status
- `GET /api/v1/metrics` - System metrics

**Player Statistics:**
- `GET /api/v1/stats/search?query=LeBron` - Search players
- `GET /api/v1/stats/leaders?category=PTS&limit=10` - Statistical leaders
- `GET /api/v1/stats/system` - Database statistics

**RAG Query:**
- `POST /api/v1/query` - Natural language questions
  ```json
  { "query": "Who are the top 5 scorers in NBA?" }
  ```

**Job Submission:**
- `POST /api/v1/scrape/submit` - Submit URLs for scraping
  ```json
  { "urls": ["https://www.basketball-reference.com/players/j/jamesle01.html"] }
  ```

## UI Features

### 1. Dashboard (/)
- System overview with key metrics
- Unique players count, processed stats, embeddings
- Real-time system resource monitoring (CPU, memory, disk)
- Kafka consumer offset tracking

### 2. Search (/search)
- Player search by name
- Display detailed statistics (PTS, REB, AST, FG%, 3P%, FT%)
- Interactive player cards with hover effects

### 3. RAG Query (/query)
- Natural language question interface
- GPT-4 powered responses with context
- Source attribution with relevance scores
- Query history tracking

### 4. Leaders (/leaders)
- Statistical rankings by category
- Interactive charts (Bar charts with Recharts)
- Top performers highlighting (gold/silver/bronze)
- Categories: PTS, REB, AST, STL, BLK, FG%, 3P%, FT%

### 5. Submit Job (/submit)
- Batch URL submission for scraping
- Job status tracking
- Example URLs provided
- Real-time progress monitoring

### 6. System Health (/health)
- Component status (MongoDB, ChromaDB, Kafka)
- System metrics visualization (CPU, memory, disk)
- Scraping statistics (total scraped, processing rate)
- Live refresh every 5 seconds

## Data Flow

### 1. Scraping Pipeline
```
User submits URLs → Kafka (raw-data topic) → Scraper Worker → MongoDB (raw collection)
```

### 2. Processing Pipeline
```
MongoDB (raw) → Kafka (processed topic) → Processor Worker → MongoDB (processed) → ChromaDB (embeddings)
```

### 3. Query Pipeline
```
User query → FastAPI → ChromaDB (semantic search) → GPT-4 (answer generation) → User response
```

## Worker Management

### Start Workers
```bash
./scripts/start_workers.sh
```

This will:
- Start scraper worker in background
- Start processor worker in background
- Save PIDs to `logs/*.pid`
- Log output to `logs/*_worker.log`

### Stop Workers
```bash
./scripts/stop_workers.sh
```

### Check Worker Status
```bash
# View logs
tail -f logs/scraper_worker.log
tail -f logs/processor_worker.log

# Check if running
ps aux | grep kafka_worker
```

## Troubleshooting

### Docker Issues
**Problem**: Containers not starting
```bash
docker-compose down
docker-compose up -d
docker-compose logs -f
```

**Problem**: Port conflicts
```bash
# Check what's using the port
sudo lsof -i :27017  # MongoDB
sudo lsof -i :9092   # Kafka
sudo lsof -i :8000   # FastAPI
sudo lsof -i :5173   # React
```

### Database Issues
**Problem**: No data in MongoDB
```bash
# Check MongoDB connection
docker exec -it ds-mt-mongodb-1 mongosh
use nba_stats
db.processed_stats.countDocuments()
```

**Problem**: Reset database
```bash
# WARNING: This deletes all data
docker exec -it ds-mt-mongodb-1 mongosh
use nba_stats
db.dropDatabase()
```

### Kafka Issues
**Problem**: Workers not consuming messages
```bash
# Check Kafka topics
docker exec -it ds-mt-kafka-1 kafka-topics --list --bootstrap-server localhost:9092

# Check consumer groups
docker exec -it ds-mt-kafka-1 kafka-consumer-groups --list --bootstrap-server localhost:9092
```

### API Issues
**Problem**: CORS errors in browser
- Verify CORS is enabled in `api/main.py`
- Check API is running on port 8000

**Problem**: 500 Internal Server Error
```bash
# Check API logs
tail -f api_server.log
```

### Frontend Issues
**Problem**: Blank page or component not loading
```bash
# Check browser console for errors
# Verify API is accessible
curl http://localhost:8000/api/v1/health

# Rebuild frontend
cd ui
npm install
npm run dev
```

## Performance Tuning

### Kafka Workers
Adjust parallelism in worker files:
```python
# scraper/kafka_worker.py
# processor/kafka_worker.py
# Increase num_workers for parallel processing
```

### MongoDB Indexing
```javascript
// Connect to MongoDB
use nba_stats

// Create indexes for faster queries
db.processed_stats.createIndex({ "player_name": 1 })
db.processed_stats.createIndex({ "stats.PTS": -1 })
db.processed_stats.createIndex({ "stats.REB": -1 })
```

### ChromaDB
Increase batch size for embedding generation:
```python
# rag/rag_system.py
# Adjust chunk_size in add_stats_batch()
```

## Shutdown Procedure

### 1. Stop Frontend
```bash
# In React terminal, press Ctrl+C
```

### 2. Stop Workers
```bash
./scripts/stop_workers.sh
```

### 3. Stop FastAPI
```bash
# In FastAPI terminal, press Ctrl+C
```

### 4. Stop Docker Services
```bash
docker-compose down
```

### 5. Deactivate Virtual Environment
```bash
deactivate
```

## Data Persistence

### MongoDB Data
- Stored in Docker volume: `ds-mt_mongodb_data`
- Persists across container restarts

### ChromaDB Data
- Stored in: `./chroma_data/`
- Persists as local directory

### Worker Logs
- Stored in: `./logs/`
- Includes PID files and output logs

## Security Notes

1. **API Key Protection**: Never commit `.env` file with OpenAI key
2. **MongoDB**: No authentication configured (development only)
3. **CORS**: Configured for localhost (adjust for production)
4. **Ports**: Ensure firewall rules for production deployment

## System Requirements

### Minimum
- CPU: 2 cores
- RAM: 4 GB
- Disk: 10 GB

### Recommended
- CPU: 4+ cores
- RAM: 8+ GB
- Disk: 20+ GB
- SSD for better I/O performance

## Support & Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Requirements**: See `REQUIREMENTS_CHECKLIST.md`
- **Project Report**: See `docs/PROJECT_REPORT.md`
