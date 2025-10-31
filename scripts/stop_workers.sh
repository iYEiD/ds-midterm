#!/bin/bash
# Stop all NBA stats system workers

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "Stopping NBA Stats System Workers..."
echo "====================================="

# Stop scraper worker
if [ -f logs/scraper_worker.pid ]; then
    SCRAPER_PID=$(cat logs/scraper_worker.pid)
    if kill -0 $SCRAPER_PID 2>/dev/null; then
        echo "Stopping Scraper Worker (PID: $SCRAPER_PID)..."
        kill $SCRAPER_PID
        rm logs/scraper_worker.pid
    else
        echo "Scraper Worker not running"
        rm logs/scraper_worker.pid 2>/dev/null
    fi
fi

# Stop processor worker
if [ -f logs/processor_worker.pid ]; then
    PROCESSOR_PID=$(cat logs/processor_worker.pid)
    if kill -0 $PROCESSOR_PID 2>/dev/null; then
        echo "Stopping Processor Worker (PID: $PROCESSOR_PID)..."
        kill $PROCESSOR_PID
        rm logs/processor_worker.pid
    else
        echo "Processor Worker not running"
        rm logs/processor_worker.pid 2>/dev/null
    fi
fi

echo ""
echo "✅ All workers stopped!"
