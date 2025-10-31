#!/bin/bash
# Start all NBA stats system workers

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate virtual environment
source venv/bin/activate

echo "Starting NBA Stats System Workers..."
echo "====================================="

# Start scraper worker
echo "Starting Kafka Scraper Worker..."
python -m scraper.kafka_scraper_worker > logs/scraper_worker.log 2>&1 &
SCRAPER_PID=$!
echo "Scraper Worker PID: $SCRAPER_PID"

# Start processor worker
echo "Starting Kafka Processor Worker..."
python -m processor.kafka_processor_worker > logs/processor_worker.log 2>&1 &
PROCESSOR_PID=$!
echo "Processor Worker PID: $PROCESSOR_PID"

# Save PIDs
echo $SCRAPER_PID > logs/scraper_worker.pid
echo $PROCESSOR_PID > logs/processor_worker.pid

echo ""
echo "✅ All workers started successfully!"
echo ""
echo "Worker PIDs saved to logs/*.pid"
echo "Logs available at:"
echo "  - Scraper: logs/scraper_worker.log"
echo "  - Processor: logs/processor_worker.log"
echo ""
echo "To stop workers, run: ./scripts/stop_workers.sh"
