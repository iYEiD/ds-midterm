# Distributed RAG-Based Web Scraper Framework

A distributed web scraping system with RAG (Retrieval-Augmented Generation) capabilities for scraping and analyzing NBA player statistics.

## 🎯 Target Use Case
Scraping NBA player statistics tables from `https://www.nba.com/stats/alltime-leaders` and similar structured data pages, with intelligent querying via natural language.

## 🏗️ Architecture

### Tech Stack
- **Distributed Computing**: Ray
- **Message Queue**: Apache Kafka
- **Databases**: 
  - MongoDB (raw and processed data storage)
  - ChromaDB (vector embeddings)
- **LLM**: OpenAI API
- **Web Framework**: FastAPI
- **Scraping**: Scrapy, Selenium, Playwright
- **Deployment**: Docker Compose

### Project Structure
```
distributed-rag-scraper/
├── scraper/              # Web scraping module
├── processor/            # Data processing module
├── rag/                  # RAG and LLM integration
├── api/                  # FastAPI service
├── infrastructure/       # Kafka, MongoDB configs
├── docker/               # Dockerfiles
├── tests/                # Unit and integration tests
├── docs/                 # Documentation and screenshots
├── docker-compose.yml    # Local infrastructure
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Docker and Docker Compose
- OpenAI API Key

### 1. Clone and Setup Virtual Environment
```bash
# Clone the repository
git clone <your-repo-url>
cd DS-MT

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key and other configurations
```

### 4. Start Infrastructure Services
```bash
docker-compose up -d
```

This will start:
- MongoDB (port 27017)
- Apache Kafka (port 9092)
- Zookeeper (port 2181)
- Ray Head Node (dashboard on port 8265)

### 5. Verify Services
```bash
# Check all containers are running
docker-compose ps

# Access Ray dashboard
open http://localhost:8265

# Test MongoDB connection
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/'); print('MongoDB connected:', client.server_info()['version'])"
```

## 📋 Development Phases

- [x] **Phase 1**: Environment & Repository Setup
- [ ] **Phase 2**: Local Infrastructure with Docker Compose
- [ ] **Phase 3**: Web Scraping Module Development
- [ ] **Phase 4**: Data Processing Module
- [ ] **Phase 5**: RAG Integration with ChromaDB and OpenAI
- [ ] **Phase 6**: FastAPI Service Development
- [ ] **Phase 7**: Load Balancing & Fault Tolerance
- [ ] **Phase 8**: Integration Testing & Documentation

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test module
pytest tests/test_scraper.py
```

## 📊 API Documentation

Once the API is running:
```bash
uvicorn api.main:app --reload
```

Access interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 Development Tips

1. **Incremental Development**: Complete and test each phase before moving forward
2. **Frequent Commits**: Commit after each working feature
3. **Test Early**: Don't accumulate untested code
4. **Monitor Resources**: Watch Docker container resources via `docker stats`
5. **API Keys**: Never commit `.env` file to Git

## 📝 Documentation

Detailed documentation for each phase can be found in:
- `docs/report.md` - Complete implementation report with screenshots
- `docs/architecture.md` - System architecture and flowcharts
- API documentation - Auto-generated via FastAPI

## 🐛 Troubleshooting

### Kafka Connection Issues
```bash
# Check Kafka logs
docker-compose logs kafka

# List topics
docker exec -it <kafka-container> kafka-topics --list --bootstrap-server localhost:9092
```

### MongoDB Issues
```bash
# Check MongoDB logs
docker-compose logs mongodb

# Access MongoDB shell
docker exec -it <mongodb-container> mongosh
```

### Ray Issues
```bash
# Check Ray dashboard
open http://localhost:8265

# View Ray logs
docker-compose logs ray-head
```

## 📄 License

This project is developed as part of a Data Science course midterm project.

## 🤝 Contributing

This is an academic project. For questions or suggestions, please contact the project maintainer.

## 📞 Support

For issues and questions:
1. Check the `docs/troubleshooting.md` guide
2. Review the project plan in `rag_scraper_plan.md`
3. Open an issue in the repository
