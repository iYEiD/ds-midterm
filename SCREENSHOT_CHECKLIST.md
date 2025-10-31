# Screenshot Checklist for Project Report

## Instructions
This document lists all screenshots needed for `docs/FINAL_PROJECT_REPORT.md`. Search for `[PLACEHOLDER: Screenshot` in that file to find where each screenshot should be inserted.

## 📸 Screenshots Needed (12 total)

### 1. System Architecture Diagram
**Location**: Section "System Architecture"  
**What to capture**: Create a diagram showing:
- React UI at top
- FastAPI in middle
- MongoDB, ChromaDB, Kafka at bottom
- Arrows showing data flow
- Worker processes on the side

**Tool suggestion**: Draw.io, Lucidchart, or simple PowerPoint diagram

---

### 2. Dashboard Page
**Location**: Section "Phase 11: Web UI - Dashboard"  
**URL**: http://localhost:5173/  
**What to capture**: 
- Full page screenshot
- Show stat cards with real numbers (50 players, etc.)
- System metrics section visible
- Recent activity timeline at bottom

**Before taking**: 
```bash
# Ensure all services running
curl http://localhost:8000/api/v1/health
```

---

### 3. Scraper Console Output
**Location**: Section "Phase 2: Web Scraping"  
**What to capture**:
```bash
tail -f logs/scraper_worker.log
```
- Terminal window showing successful scraping logs
- Include timestamp, player names, success messages

---

### 4. MongoDB Database View
**Location**: Section "Phase 3: Data Processing"  
**What to capture**:
```bash
docker exec -it ds-mt-mongodb-1 mongosh
use nba_stats
db.processed_stats.find().limit(1).pretty()
```
- MongoDB shell or Compass showing `processed_stats` collection
- One full document visible with all fields
- Document count visible

---

### 5. RAG Query Interface
**Location**: Section "Phase 4: RAG System"  
**URL**: http://localhost:5173/query  
**What to capture**:
- Query input box with example question: "Who are the top 5 scorers?"
- GPT-4 response showing answer
- Sources section with relevance scores
- Query history at bottom

---

### 6. Swagger API Documentation
**Location**: Section "Phase 5: REST API"  
**URL**: http://localhost:8000/docs  
**What to capture**:
- List of all endpoints (collapsed)
- One expanded endpoint showing:
  - Request parameters
  - Response schema
  - "Try it out" button

---

### 7. System Health Monitor - Kafka Metrics
**Location**: Section "Phase 6: Load Balancing"  
**URL**: http://localhost:5173/health  
**What to capture**:
- Health cards showing all services green
- Scraping statistics section
- System metrics with progress bars

---

### 8. Test Execution Results
**Location**: Section "Phase 7: Testing"  
**What to capture**:
```bash
pytest tests/ -v
```
- Terminal showing pytest output
- All tests passed (green checkmarks)
- Test count and timing

---

### 9. Search Results Page
**Location**: Section "Phase 11: Web UI - Search"  
**URL**: http://localhost:5173/search  
**What to capture**:
- Search bar with "LeBron James" entered
- Multiple player cards displayed
- Stats visible on cards (PTS, REB, AST, etc.)

---

### 10. Statistical Leaders Chart
**Location**: Section "Phase 11: Web UI - Leaders"  
**URL**: http://localhost:5173/leaders  
**What to capture**:
- Category dropdown showing "Points" selected
- Bar chart with top 10 players
- Table below with rankings and gold/silver/bronze medals

---

### 11. Job Submission Form
**Location**: Section "Phase 11: Web UI - Submit Job"  
**URL**: http://localhost:5173/submit  
**What to capture**:
- Textarea with example URLs filled in
- "Submit Job" and "Load Example URLs" buttons
- Job ID result after submission (if possible)

---

### 12. Docker Containers Running
**Location**: Section "Deployment Architecture"  
**What to capture**:
```bash
docker-compose ps
```
- Terminal showing all 3 containers:
  - ds-mt-mongodb-1 (Up)
  - ds-mt-kafka-1 (Up)
  - ds-mt-zookeeper-1 (Up)
- Port mappings visible

---

## 🔧 How to Take Screenshots

### For Web Pages (UI Screenshots)
1. Use browser built-in screenshot (F12 → Ctrl+Shift+P → "Capture full size screenshot")
2. Or use browser extension like "Full Page Screen Capture"
3. Crop to remove browser chrome if desired
4. Save as PNG format

### For Terminal/Console
1. Use native screenshot tool (Linux: Screenshot app, Mac: Cmd+Shift+4, Windows: Snipping Tool)
2. Make terminal font size readable (14-16pt)
3. Ensure full command and output visible
4. Save as PNG format

### For Diagrams
1. Create using online tool (draw.io recommended)
2. Export as PNG at 150-300 DPI
3. Ensure text is readable

## 📝 Inserting Screenshots into Report

1. Save all screenshots in `docs/images/` directory (create if needed)
2. Name files descriptively:
   - `architecture_diagram.png`
   - `dashboard_overview.png`
   - `rag_query_example.png`
   - etc.

3. Replace placeholders in `docs/FINAL_PROJECT_REPORT.md`:
```markdown
# Before:
**[PLACEHOLDER: Screenshot - Dashboard page showing all metrics]**

# After:
![Dashboard Overview](images/dashboard_overview.png)
*Figure 1: Dashboard showing system metrics and statistics*
```

## ✅ Verification Checklist

Before taking screenshots, ensure:
- [ ] All Docker containers running (`docker-compose ps`)
- [ ] FastAPI server running (check http://localhost:8000/api/v1/health)
- [ ] React UI running (check http://localhost:5173)
- [ ] Workers running (`ps aux | grep kafka_worker`)
- [ ] Database has data (`curl http://localhost:8000/api/v1/stats/system`)

## 📊 Screenshot Quality Standards

- **Resolution**: Minimum 1920x1080 for web pages
- **Format**: PNG (lossless compression)
- **Text**: Must be clearly readable
- **Context**: Show enough context (headers, navigation, etc.)
- **Annotations**: Add arrows/boxes if highlighting specific features (optional)

## 🎨 Optional: Professional Touch

For better presentation, consider:
- Adding subtle drop shadows to UI screenshots
- Highlighting important sections with colored boxes
- Adding figure captions below each image
- Consistent border/padding around all screenshots

---

**Total Screenshots**: 12  
**Estimated Time**: 30-45 minutes  
**Tools Needed**: Browser, Terminal, Screenshot utility, Optional diagram tool
