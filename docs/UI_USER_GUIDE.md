# NBA Stats Scraper - UI User Guide

## Available Features

### 1. Dashboard (/)
- **System Overview**: View total unique players, processed stats, embeddings, and raw documents
- **System Resources**: Real-time CPU, memory, and disk usage
- **Recent Activity**: System status indicators

**Current Data**: 50 unique players with stats already loaded

### 2. Search (/search)
- **Player Search**: Search for players by name
- **Stats Display**: View comprehensive stats including:
  - Games Played (GP)
  - Points (PTS), Rebounds (REB), Assists (AST)
  - Field Goal %, 3-Point %, Free Throw %
  - Steals (STL), Blocks (BLK)

**Try Searching**: LeBron James, Kobe Bryant, Stephen Curry, John Stockton, etc.

### 3. RAG Query (/query)
- **Natural Language Questions**: Ask questions about NBA players in plain English
- **AI-Powered Responses**: Get detailed answers from GPT-4
- **Source Citations**: See which player stats were used to generate the answer
- **Query History**: Track your recent questions

**Example Questions**:
- "Who are the top 5 scorers in the NBA?"
- "Compare LeBron James and Stephen Curry shooting percentages"
- "Which players average more than 10 rebounds per game?"
- "Tell me about the best three-point shooters"
- "Who has the highest field goal percentage?"

### 4. Leaders (/leaders)
- **Statistical Rankings**: View top performers in different categories
- **Interactive Charts**: Bar charts showing leader comparisons
- **Filterable**: Choose category and limit (5, 10, 15, 20 players)

**Available Categories**:
- Total Points (PTS)
- Total Rebounds (REB)
- Total Assists (AST)
- Total Steals (STL)
- Total Blocks (BLK)
- Field Goal % (FG%)
- Three Point % (3P%)
- Free Throw % (FT%)

### 5. Submit Job (/submit)
- **Add New Players**: Submit NBA.com stats URLs for scraping
- **Batch Processing**: Add multiple URLs at once
- **Background Processing**: Kafka workers process jobs asynchronously

**Note**: Currently, 50 players from NBA.com all-time leaders are already in the database. The system detects duplicate URLs to avoid re-scraping.

### 6. System Health (/health)
- **Service Status**: MongoDB, ChromaDB, and Kafka connection status
- **Real-time Metrics**: CPU, memory, disk usage with visual indicators
- **Scraping Statistics**: View scraping and processing rates
- **System Info**: Version information and uptime

## Currently Available Players

The database contains 50 NBA players including all-time greats:
- **Top Scorers**: LeBron James, Karl Malone, Kobe Bryant, Michael Jordan
- **Assist Leaders**: John Stockton, Jason Kidd, Chris Paul, Steve Nash
- **Rebounding Leaders**: Various all-time greats
- **Defensive Specialists**: Steals and blocks leaders

## How to Use

### Basic Workflow:
1. **Start Here**: Check the Dashboard to see system status
2. **Explore Data**: Use Search to find specific players
3. **Ask Questions**: Use RAG Query for natural language insights
4. **Compare Stats**: View Leaders to see rankings
5. **Monitor System**: Check System Health for performance metrics

### Best Practices:
- **Search**: Type player names (first or last name works)
- **RAG Queries**: Ask complete questions for better answers
- **Leaders**: Change categories to explore different stats
- **Refresh**: Data updates automatically every 5-30 seconds

## Technical Details

- **Backend API**: Running on http://localhost:8000
- **Frontend**: React + Vite on http://localhost:5173
- **Database**: MongoDB with 50 processed player stats
- **Vector Store**: ChromaDB with 50 embeddings
- **AI**: GPT-4 for natural language responses
- **Workers**: Kafka consumers for distributed processing

## Troubleshooting

### If Search Shows "N/A":
- Refresh the page
- Check that the API is running (green indicator in navbar)
- Try searching for: "LeBron James", "John Stockton", or "Kobe Bryant"

### If RAG Query Doesn't Show Answer:
- Make sure to click "Ask Question" button
- Wait a few seconds for GPT-4 to process
- Check the navbar health indicator is green

### If Dashboard is Empty:
- The data should show: 50 players, 50 processed stats, 50 embeddings
- If not, restart the API server

## Need More Data?

To add more players, you would need NBA.com stats URLs in the format:
```
https://www.nba.com/stats/alltime-leaders?SeasonType=Regular%20Season&PerMode=Totals&StatCategory=[STAT]
```

The system currently has data from steals (STL) category leaders, which includes 50 of the NBA's all-time great players.
