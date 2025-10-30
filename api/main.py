"""
FastAPI main application.
Provides REST API for NBA stats scraping system with RAG integration.
"""
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.storage import get_storage
from rag.vector_store import get_vector_store
from rag.retriever import StatsRetriever
from rag.llm_augmenter import LLMAugmenter
from orchestrator import JobOrchestrator

# Initialize FastAPI app
app = FastAPI(
    title="NBA Stats Scraper API",
    description="Distributed RAG-based NBA statistics scraping and query system",
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
storage = get_storage()
vector_store = get_vector_store()
retriever = StatsRetriever()
llm_augmenter = LLMAugmenter()
orchestrator = JobOrchestrator()

# Request/Response Models
class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query about NBA stats")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to retrieve")

class QueryResponse(BaseModel):
    query: str
    answer: str
    context: List[Dict[str, Any]]
    tokens_used: int
    
class ScrapingJobRequest(BaseModel):
    urls: List[str] = Field(..., description="URLs to scrape")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")

class ScrapingJobResponse(BaseModel):
    status: str
    submitted: int
    skipped: int
    message: str

class PlayerStatsResponse(BaseModel):
    player_name: str
    stats: Dict[str, Any]
    metadata: Dict[str, Any]

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Check API and system health."""
    try:
        # Check MongoDB
        mongo_stats = storage.get_stats_count()
        
        # Check ChromaDB
        chroma_count = vector_store.count()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "mongodb": {
                    "status": "connected",
                    "raw_documents": mongo_stats["raw_data_count"],
                    "processed_stats": mongo_stats["processed_stats_count"],
                    "unique_players": mongo_stats["unique_players"]
                },
                "chromadb": {
                    "status": "connected",
                    "embeddings": chroma_count
                },
                "kafka": {
                    "status": "connected"  # Could add actual Kafka health check
                }
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# System stats endpoint
@app.get("/api/v1/stats/system")
async def get_system_stats():
    """Get system-wide statistics."""
    try:
        mongo_stats = storage.get_stats_count()
        chroma_count = vector_store.count()
        
        return {
            "database": mongo_stats,
            "vector_store": {
                "total_embeddings": chroma_count
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# RAG Query endpoint
@app.post("/api/v1/query", response_model=QueryResponse)
async def query_stats(request: QueryRequest):
    """
    Natural language query using RAG system.
    
    Example queries:
    - "Who is the all-time leading scorer?"
    - "Compare LeBron James and Michael Jordan"
    - "Show me top assists leaders"
    """
    try:
        # Generate answer with LLM (it handles retrieval internally)
        llm_response = llm_augmenter.generate_response(
            query=request.query, 
            top_k=request.top_k
        )
        
        # Format context from retrieved stats
        context = [
            {
                "player": result.get("metadata", {}).get("player_name", "Unknown"),
                "stats": result.get("document", ""),
                "metadata": result.get("metadata", {}),
                "similarity": result.get("similarity_score", 0.0)
            }
            for result in llm_response.get("retrieved_stats", [])
        ]
        
        return QueryResponse(
            query=request.query,
            answer=llm_response.get("response", "No response generated"),
            context=context,
            tokens_used=llm_response.get("tokens_used", 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

# Player stats endpoint
@app.get("/api/v1/stats/player/{player_name}")
async def get_player_stats(player_name: str):
    """Get statistics for a specific player."""
    try:
        # Search in MongoDB
        player_stats = storage.processed_data.find_one(
            {"player_name": {"$regex": f"^{player_name}$", "$options": "i"}}
        )
        
        if not player_stats:
            raise HTTPException(status_code=404, detail=f"Player '{player_name}' not found")
        
        # Remove MongoDB _id
        player_stats.pop("_id", None)
        
        return player_stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Leaders endpoint
@app.get("/api/v1/stats/leaders")
async def get_leaders(
    category: str = Query(..., description="Stat category (e.g., PTS, AST, REB)"),
    limit: int = Query(10, ge=1, le=50, description="Number of leaders to return")
):
    """Get top players by statistical category."""
    try:
        # Query MongoDB for leaders
        stat_field = f"stats.{category}"
        
        leaders = list(storage.processed_data.find(
            {stat_field: {"$exists": True}},
            {"_id": 0}
        ).sort(stat_field, -1).limit(limit))
        
        if not leaders:
            raise HTTPException(
                status_code=404, 
                detail=f"No stats found for category '{category}'"
            )
        
        return {
            "category": category,
            "count": len(leaders),
            "leaders": leaders
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Search endpoint
@app.get("/api/v1/stats/search")
async def search_stats(
    query: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Max results")
):
    """Search processed stats by player name or metadata."""
    try:
        # Text search in MongoDB
        results = list(storage.processed_data.find(
            {
                "$or": [
                    {"player_name": {"$regex": query, "$options": "i"}},
                    {"metadata.stat_category": {"$regex": query, "$options": "i"}}
                ]
            },
            {"_id": 0}
        ).limit(limit))
        
        return {
            "query": query,
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Raw data endpoints
@app.get("/api/v1/raw/list")
async def list_raw_data(
    skip: int = Query(0, ge=0, description="Skip N documents"),
    limit: int = Query(10, ge=1, le=100, description="Max results")
):
    """List all scraped URLs with pagination."""
    try:
        raw_docs = list(storage.raw_data.find(
            {},
            {"_id": 0, "html_content": 0}  # Exclude large HTML field
        ).skip(skip).limit(limit))
        
        total = storage.raw_data.count_documents({})
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "count": len(raw_docs),
            "documents": raw_docs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/raw/{url_id}")
async def get_raw_data(url_id: str):
    """Get raw scraped HTML by URL ID."""
    try:
        raw_doc = storage.raw_data.find_one(
            {"url": url_id},
            {"_id": 0}
        )
        
        if not raw_doc:
            raise HTTPException(status_code=404, detail=f"URL '{url_id}' not found")
        
        return raw_doc
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Scraping job submission endpoint
@app.post("/api/v1/scrape/submit", response_model=ScrapingJobResponse)
async def submit_scraping_job(request: ScrapingJobRequest):
    """
    Submit URLs for scraping.
    Workers will process them asynchronously via Kafka.
    """
    try:
        result = orchestrator.submit_scraping_job(
            urls=request.urls,
            metadata=request.metadata or {}
        )
        
        return ScrapingJobResponse(
            status="success" if result["submitted"] > 0 else "no_new_urls",
            submitted=result["submitted"],
            skipped=result["skipped"],
            message=f"Submitted {result['submitted']} URLs to Kafka queue"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job submission failed: {str(e)}")

# Root endpoint
@app.get("/")
async def root():
    """API root with basic info."""
    return {
        "name": "NBA Stats Scraper API",
        "version": "1.0.0",
        "docs": "/api/v1/docs",
        "health": "/api/v1/health",
        "endpoints": {
            "query": "POST /api/v1/query",
            "player_stats": "GET /api/v1/stats/player/{name}",
            "leaders": "GET /api/v1/stats/leaders?category={PTS|AST|REB}",
            "search": "GET /api/v1/stats/search?query={text}",
            "submit_scraping": "POST /api/v1/scrape/submit",
            "system_stats": "GET /api/v1/stats/system"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
