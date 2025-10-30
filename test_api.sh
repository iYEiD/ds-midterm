#!/bin/bash
# Test script for FastAPI endpoints

BASE_URL="http://localhost:8000"

echo "========================================"
echo "NBA Stats API - Endpoint Tests"
echo "========================================"
echo ""

echo "1. Health Check"
echo "---"
curl -s "$BASE_URL/api/v1/health" | python -m json.tool
echo -e "\n"

echo "2. System Stats"
echo "---"
curl -s "$BASE_URL/api/v1/stats/system" | python -m json.tool
echo -e "\n"

echo "3. Top 3 Points Leaders"
echo "---"
curl -s "$BASE_URL/api/v1/stats/leaders?category=PTS&limit=3" | python -m json.tool | head -40
echo -e "\n"

echo "4. Search for 'Karl Malone'"
echo "---"
curl -s "$BASE_URL/api/v1/stats/search?query=Karl&limit=2" | python -m json.tool | head -40
echo -e "\n"

echo "5. RAG Query: 'Who is the all-time assist leader?'"
echo "---"
curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who is the all-time assist leader?", "top_k": 3}' | python -m json.tool | head -50
echo -e "\n"

echo "6. RAG Query: 'Compare John Stockton and Chris Paul'"
echo "---"
curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Compare John Stockton and Chris Paul in assists", "top_k": 3}' | python -m json.tool | head -50
echo -e "\n"

echo "========================================"
echo "All tests completed!"
echo "========================================"
