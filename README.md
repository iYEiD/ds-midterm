# 🏀 Distributed RAG-Based NBA Stats Scraper# Distributed RAG-Based Web Scraper Framework



A **production-grade distributed web scraping system** with RAG (Retrieval-Augmented Generation) capabilities for NBA statistics. Built with Kafka, MongoDB, ChromaDB, and OpenAI GPT-4.A distributed web scraping system with RAG (Retrieval-Augmented Generation) capabilities for scraping and analyzing NBA player statistics.



[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)## 🎯 Target Use Case

[![FastAPI](https://img.shields.io/badge/FastAPI-0.120.2-green.svg)](https://fastapi.tiangolo.com/)Scraping NBA player statistics tables from `https://www.nba.com/stats/alltime-leaders` and similar structured data pages, with intelligent querying via natural language.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🏗️ Architecture

## 🌟 Features

### Tech Stack

- ⚡ **Distributed Scraping**: Kafka-based event-driven architecture with horizontal scaling- **Distributed Computing**: Ray

- 🤖 **AI-Powered Queries**: Natural language queries using OpenAI GPT-4 and vector search- **Message Queue**: Apache Kafka

- 🔄 **Fault Tolerance**: Exponential backoff retry logic and dead letter queue- **Databases**: 

- 📊 **RESTful API**: 15+ endpoints for data access and system management  - MongoDB (raw and processed data storage)

- 📈 **Monitoring**: Comprehensive metrics (CPU, memory, database stats)  - ChromaDB (vector embeddings)

- 🧪 **Tested**: Complete E2E test suite with 100% pass rate- **LLM**: OpenAI API

- 🐳 **Containerized**: Docker Compose for easy deployment- **Web Framework**: FastAPI

- **Scraping**: Scrapy, Selenium, Playwright

## 🚀 Quick Start- **Deployment**: Docker Compose



```bash### Project Structure

# 1. Clone and setup```

git clone https://github.com/iYEiD/ds-midterm.gitdistributed-rag-scraper/

cd DS-MT├── scraper/              # Web scraping module

├── processor/            # Data processing module

# 2. Start infrastructure├── rag/                  # RAG and LLM integration

docker-compose up -d├── api/                  # FastAPI service

├── infrastructure/       # Kafka, MongoDB configs

# 3. Setup Python environment├── docker/               # Dockerfiles

python -m venv venv├── tests/                # Unit and integration tests

source venv/bin/activate├── docs/                 # Documentation and screenshots

pip install -r requirements.txt├── docker-compose.yml    # Local infrastructure

├── requirements.txt      # Python dependencies

# 4. Start API server└── README.md            # This file

uvicorn api.main:app --host 0.0.0.0 --port 8000```



# 5. Test the system## 🚀 Quick Start

curl http://localhost:8000/api/v1/health

```### Prerequisites

- Python 3.10+

## 📚 Documentation- Docker and Docker Compose

- OpenAI API Key

- **[Complete Project Report](docs/PROJECT_REPORT.md)** - Comprehensive system documentation

- **[Testing Guide](TESTING_GUIDE.md)** - How to test the distributed system### 1. Clone and Setup Virtual Environment

- **[API Documentation](http://localhost:8000/api/v1/docs)** - Interactive API docs (when server running)```bash

# Clone the repository

## 🏗️ Architecturegit clone <your-repo-url>

cd DS-MT

```

User → Nginx → FastAPI → Orchestrator → Kafka Queue# Create virtual environment

                   ↓                          ↓python -m venv venv

                MongoDB ←─ Scraper Workers ←──┘source venv/bin/activate  # On Windows: venv\Scripts\activate

                   ↓              ↓```

              ChromaDB ←─ Processor Workers ←── Kafka Results

                   ↓### 2. Install Dependencies

              RAG System (GPT-4) → API Response```bash

```pip install -r requirements.txt

```

## 💻 Usage Examples

### 3. Configure Environment Variables

### Natural Language Queries (RAG)```bash

```bashcp .env.example .env

curl -X POST http://localhost:8000/api/v1/query \# Edit .env and add your OpenAI API key and other configurations

  -H "Content-Type: application/json" \```

  -d '{"query": "Who is the all-time leading scorer?", "top_k": 5}'

```### 4. Start Infrastructure Services

```bash

### Get Leaders by Categorydocker-compose up -d

```bash```

curl "http://localhost:8000/api/v1/stats/leaders?category=PTS&limit=10"

```This will start:

- MongoDB (port 27017)

### Submit Scraping Job- Apache Kafka (port 9092)

```bash- Zookeeper (port 2181)

python orchestrator.py --urls "https://www.nba.com/stats/alltime-leaders?StatCategory=REB" --monitor- Ray Head Node (dashboard on port 8265)

```

### 5. Verify Services

## 🧪 Testing```bash

# Check all containers are running

```bashdocker-compose ps

# Run comprehensive E2E test

python tests/test_comprehensive_e2e.py# Access Ray dashboard

open http://localhost:8265

# Test API endpoints

./test_api.sh# Test MongoDB connection

python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/'); print('MongoDB connected:', client.server_info()['version'])"

# Test distributed workers```

python tests/test_distributed_e2e.py

```## 📋 Development Phases



## 🛠️ Technologies- [x] **Phase 1**: Environment & Repository Setup

- [ ] **Phase 2**: Local Infrastructure with Docker Compose

**Core**: Python 3.12, FastAPI, Apache Kafka 7.5, MongoDB 7.0, ChromaDB  - [ ] **Phase 3**: Web Scraping Module Development

**AI/ML**: OpenAI GPT-4, text-embedding-3-small (1536 dimensions)  - [ ] **Phase 4**: Data Processing Module

**Scraping**: Scrapy 2.13, Playwright 1.55, BeautifulSoup  - [ ] **Phase 5**: RAG Integration with ChromaDB and OpenAI

**Monitoring**: psutil, loguru, prometheus-client  - [ ] **Phase 6**: FastAPI Service Development

**Deployment**: Docker, Docker Compose, Nginx- [ ] **Phase 7**: Load Balancing & Fault Tolerance

- [ ] **Phase 8**: Integration Testing & Documentation

## 📊 Current Dataset

## 🧪 Testing

- **50 NBA Players** with comprehensive career statistics

- **6 Statistical Categories**: PTS, AST, REB, STL, BLK, etc.```bash

- **50 Vector Embeddings** (1536 dimensions each)# Run all tests

- **Source**: NBA.com official statisticspytest



## 📁 Project Structure# Run with coverage

pytest --cov=. --cov-report=html

```

DS-MT/# Run specific test module

├── api/                  # FastAPI REST APIpytest tests/test_scraper.py

├── scraper/              # Distributed web scraping```

├── processor/            # Data processing pipeline

├── rag/                  # RAG system (vector store, LLM)## 📊 API Documentation

├── monitoring/           # Metrics and health checks

├── infrastructure/       # Nginx, configsOnce the API is running:

├── tests/                # E2E test suites```bash

├── docs/                 # Documentationuvicorn api.main:app --reload

├── orchestrator.py       # Job coordinator```

└── docker-compose.yml    # Infrastructure services

```Access interactive API documentation at:

- Swagger UI: http://localhost:8000/docs

## 🎯 Key Features- ReDoc: http://localhost:8000/redoc



### 1. Distributed Architecture## 🔧 Development Tips

- Kafka consumer groups for automatic load balancing

- Horizontal scaling (add more workers dynamically)1. **Incremental Development**: Complete and test each phase before moving forward

- No single point of failure2. **Frequent Commits**: Commit after each working feature

3. **Test Early**: Don't accumulate untested code

### 2. RAG System4. **Monitor Resources**: Watch Docker container resources via `docker stats`

1. User query → OpenAI embedding5. **API Keys**: Never commit `.env` file to Git

2. ChromaDB similarity search → Top-K results

3. Context + query → GPT-4 prompt## 📝 Documentation

4. Natural language answer with sources

Detailed documentation for each phase can be found in:

### 3. Fault Tolerance- `docs/report.md` - Complete implementation report with screenshots

- Exponential backoff retry (3 attempts)- `docs/architecture.md` - System architecture and flowcharts

- Dead letter queue for permanent failures- API documentation - Auto-generated via FastAPI

- Health monitoring and graceful degradation

## 🐛 Troubleshooting

## 📈 Performance

### Kafka Connection Issues

- **Scraping**: 5-10 pages/minute```bash

- **Processing**: 20-30 seconds (URL → embeddings)# Check Kafka logs

- **API Latency**: 50-200ms (database queries)docker-compose logs kafka

- **RAG Queries**: 2-5 seconds (includes OpenAI)

- **Scalability**: Tested with 10 parallel workers# List topics

docker exec -it <kafka-container> kafka-topics --list --bootstrap-server localhost:9092

## 🐛 Troubleshooting```



```bash### MongoDB Issues

# Check services```bash

docker-compose ps# Check MongoDB logs

docker-compose logs mongodb

# View logs

tail -f api_server.log# Access MongoDB shell

docker exec -it <mongodb-container> mongosh

# Test Kafka```

docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

### Ray Issues

# Test MongoDB```bash

mongosh mongodb://localhost:27017/nba_scraper# Check Ray dashboard

```open http://localhost:8265



## 📚 Additional Resources# View Ray logs

docker-compose logs ray-head

- [Original Project Plan](rag_scraper_plan.md)```

- [API Testing Script](test_api.sh)

- [Nginx Config](infrastructure/nginx.conf)## 📄 License



## 👤 AuthorThis project is developed as part of a Data Science course midterm project.



**iYEiD**  ## 🤝 Contributing

GitHub: [@iYEiD](https://github.com/iYEiD)  

Repository: [ds-midterm](https://github.com/iYEiD/ds-midterm)This is an academic project. For questions or suggestions, please contact the project maintainer.



## 📄 License## 📞 Support



MIT License - see LICENSE file for detailsFor issues and questions:

1. Check the `docs/troubleshooting.md` guide

---2. Review the project plan in `rag_scraper_plan.md`

3. Open an issue in the repository

**Status**: ✅ Production Ready | 🧪 Fully Tested | 📊 50 Players | 🤖 AI-Powered

**Built for Data Science Midterm Project - October 2025**
