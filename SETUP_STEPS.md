# 🔧 Manual Setup Steps

This file contains the manual steps you need to perform before continuing with the project.

## ✅ Phase 1 Completed - Next Steps

### Step 1: Create Virtual Environment
```bash
cd /home/yeid/DS-MT
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: Installation may take 5-10 minutes as it includes large packages like Ray, Scrapy, and Playwright.

### Step 3: Install Playwright Browsers (Required for JavaScript-heavy sites)
```bash
playwright install
```

### Step 4: Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual values
nano .env  # or use your preferred editor
```

**Important**: You MUST add your OpenAI API key in the `.env` file:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### Step 5: Initialize Git Repository (Optional but Recommended)
```bash
git init
git add .
git commit -m "Initial project setup - Phase 1 complete"
```

If you have a remote repository:
```bash
git remote add origin <your-repo-url>
git push -u origin main
```

### Step 6: Verify Python Environment
```bash
# Verify all critical packages are installed
python -c "import scrapy; print('Scrapy:', scrapy.__version__)"
python -c "import ray; print('Ray:', ray.__version__)"
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import pymongo; print('PyMongo:', pymongo.__version__)"
python -c "import chromadb; print('ChromaDB:', chromadb.__version__)"
```

All commands should run without errors and display version numbers.

---

## 📋 Checklist Before Moving to Phase 2

- [ ] Virtual environment created and activated
- [ ] All dependencies installed successfully
- [ ] Playwright browsers installed
- [ ] `.env` file created and configured with OpenAI API key
- [ ] Git repository initialized (optional)
- [ ] All import tests passed

---

## 🚀 What's Next?

Once you've completed all the steps above, let me know and I'll proceed with:

**Phase 2: Local Infrastructure with Docker Compose**
- Create docker-compose.yml for MongoDB, Kafka, Zookeeper, and Ray
- Set up networking between containers
- Create initialization scripts
- Test infrastructure connectivity

---

## ⚠️ Troubleshooting

### If pip install fails:
```bash
# Try installing in smaller groups
pip install scrapy beautifulsoup4 lxml selenium playwright
pip install "ray[default]"
pip install kafka-python
pip install pymongo chromadb
pip install openai
pip install fastapi uvicorn[standard] pydantic
```

### If you don't have an OpenAI API key:
1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Add it to your `.env` file

### If Ray installation fails on your system:
Ray has specific system requirements. Check: https://docs.ray.io/en/latest/ray-overview/installation.html

---

## 📞 Questions?

If you encounter any issues with these setup steps, please let me know and I can help troubleshoot!

---

---

# 🐳 Phase 2: Docker Infrastructure Setup

## Quick Start (Using Helper Script)
```bash
cd /home/yeid/DS-MT
./manage_infrastructure.sh start
```

Or manually:

## Step 1: Start All Infrastructure Services
```bash
cd /home/yeid/DS-MT
docker-compose up -d
```

This will start:
- ✅ Zookeeper (Kafka dependency) - Port 2181
- ✅ Kafka (Message broker) - Port 9092
- ✅ MongoDB (Database) - Port 27017
- ✅ Ray Head Node (Distributed computing) - Port 8265

## Step 2: Verify All Containers Are Running
```bash
docker-compose ps
```

You should see all services with status "Up" or "healthy".

## Step 3: Check Container Logs (If Any Issues)
```bash
# Check all logs
docker-compose logs

# Check specific service
docker-compose logs kafka
docker-compose logs mongodb
docker-compose logs ray-head
```

## Step 4: Verify Kafka Topics Were Created
```bash
docker exec -it nba-kafka kafka-topics --bootstrap-server localhost:9092 --list
```

You should see:
- scraping-tasks
- scraping-results
- processing-tasks

## Step 5: Verify MongoDB Connection and Collections
```bash
docker exec -it nba-mongodb mongosh nba_scraper --eval "db.getCollectionNames()"
```

You should see collections:
- raw_scraped_data
- processed_stats
- scraping_metadata
- query_history

## Step 6: Access Ray Dashboard
Open your browser and go to:
```
http://localhost:8265
```

You should see the Ray dashboard with the cluster overview.

## Step 7: Run Automated Verification Script
```bash
# Make sure your virtual environment is activated
source venv/bin/activate

# Run the verification script
python verify_infrastructure.py
```

This script will automatically test MongoDB, Kafka, and Ray connections and show you a summary.

---

## 📋 Phase 2 Checklist

- [ ] All Docker containers started successfully
- [ ] All containers showing healthy status
- [ ] Kafka topics created (scraping-tasks, scraping-results, processing-tasks)
- [ ] MongoDB collections created with indexes
- [ ] Ray dashboard accessible at http://localhost:8265
- [ ] Python can connect to MongoDB
- [ ] Python can connect to Kafka

---

## 🚀 What's Next?

Once all Phase 2 checks pass, let me know and I'll proceed with:

**Phase 3: Web Scraping Module Development**
- Create NBA stats spider
- Implement URL manager with Kafka
- Set up distributed scraping with Ray
- Store raw data in MongoDB

---

## ⚠️ Troubleshooting Phase 2

### If containers fail to start:
```bash
# Check Docker daemon is running
docker info

# Check for port conflicts
sudo lsof -i :9092  # Kafka
sudo lsof -i :27017 # MongoDB
sudo lsof -i :8265  # Ray

# Remove old containers and volumes if needed
docker-compose down -v
docker-compose up -d
```

### If Kafka topics are not created:
```bash
# Check kafka-init logs
docker-compose logs kafka-init

# Manually create topics if needed
docker exec -it nba-kafka kafka-topics --bootstrap-server localhost:9092 --create --topic scraping-tasks --partitions 3 --replication-factor 1
```

### If MongoDB init script didn't run:
```bash
# The script only runs on first container creation
# To re-run, you need to remove the volume:
docker-compose down
docker volume rm nba-mongo-data
docker-compose up -d mongodb
```

### If Ray dashboard is not accessible:
```bash
# Check Ray logs
docker-compose logs ray-head

# Verify Ray is running
docker exec -it nba-ray-head ray status
```

---

---

# 🕷️ Phase 3: Web Scraping Module Testing

## What Was Built:

Phase 3 includes:
- ✅ **Configuration module** (`config.py`) - Centralized settings management
- ✅ **MongoDB Storage** (`scraper/storage.py`) - Database operations for raw and processed data
- ✅ **Kafka URL Manager** (`scraper/url_manager.py`) - Distributed URL queue management
- ✅ **NBA Scraper** (`scraper/nba_scraper.py`) - Web scraper with retry logic and rate limiting
- ✅ **Distributed Scraper** (`scraper/distributed_scraper.py`) - Ray-based parallel scraping
- ✅ **Test Suite** (`tests/test_scraper.py`) - Comprehensive tests for all components

## Step 1: Run the Test Suite

```bash
# Make sure you're in the project directory with venv activated
cd /home/yeid/DS-MT
source venv/bin/activate

# Run the comprehensive test suite
python tests/test_scraper.py
```

This will test:
1. ✅ Configuration loading
2. ✅ MongoDB storage operations
3. ✅ Kafka URL submission and retrieval
4. ✅ NBA scraper functionality
5. ✅ Ray distributed scraping

## Step 2: Test Individual Components (Optional)

### Test Basic Scraper
```bash
# Scrape NBA stats page
python scraper/nba_scraper.py
```

### Test Distributed Scraper
```bash
# Test Ray-based parallel scraping
python scraper/distributed_scraper.py
```

## Step 3: Check the Data in MongoDB

```bash
# View scraped data
docker exec -it nba-mongodb mongosh nba_scraper --eval "db.raw_scraped_data.find().limit(3).pretty()"

# Count documents
docker exec -it nba-mongodb mongosh nba_scraper --eval "db.raw_scraped_data.countDocuments({})"

# View scraping metadata
docker exec -it nba-mongodb mongosh nba_scraper --eval "db.scraping_metadata.find().pretty()"
```

## Step 4: Check Kafka Topics

```bash
# View messages in scraping-tasks topic
docker exec -it nba-kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic scraping-tasks --from-beginning --max-messages 5

# View messages in scraping-results topic
docker exec -it nba-kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic scraping-results --from-beginning --max-messages 5
```

## Step 5: Check Ray Dashboard

Open your browser and visit:
```
http://localhost:8265
```

You should see:
- Active workers
- Task execution history
- Resource utilization

## Step 6: View Logs

```bash
# View application logs
tail -f logs/app.log

# Or view test logs
tail -f logs/test_scraper.log
```

---

## 📋 Phase 3 Checklist

- [ ] Test suite runs successfully
- [ ] Can scrape NBA stats pages
- [ ] Data is stored in MongoDB
- [ ] URLs are submitted to Kafka
- [ ] Ray distributed scraping works
- [ ] Ray dashboard shows active workers
- [ ] Logs are being created

---

## ⚠️ Troubleshooting Phase 3

### If tests fail with "OpenAI API key not set":
This is expected! The OpenAI key is only needed for Phase 5 (RAG). You can ignore this for now.

### If scraping fails with connection errors:
```bash
# Check your internet connection
ping www.nba.com

# Check if NBA.com is accessible
curl -I https://www.nba.com/stats
```

### If Ray fails to initialize:
```bash
# Make sure Ray container is running
docker-compose ps ray-head

# Check Ray logs
docker-compose logs ray-head

# Try restarting Ray
docker-compose restart ray-head
```

### If MongoDB connection fails:
```bash
# Verify MongoDB is running
docker-compose ps mongodb

# Test connection
docker exec -it nba-mongodb mongosh --eval "db.adminCommand('ping')"
```

### If Kafka producer fails:
```bash
# Verify Kafka is running
docker-compose ps kafka

# Check Kafka logs
docker-compose logs kafka
```

---

## 🚀 What's Next?

Once all Phase 3 tests pass, you're ready for:

**Phase 4: Data Processing Module**
- HTML parser for NBA tables
- Data normalization and cleaning
- Ray-based distributed processing
- Storage of clean structured data
