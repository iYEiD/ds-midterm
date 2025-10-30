#!/bin/bash
# Helper script to manage infrastructure services

set -e

COMPOSE_FILE="docker-compose.yml"

show_usage() {
    echo "Usage: $0 {start|stop|restart|status|logs|clean}"
    echo ""
    echo "Commands:"
    echo "  start    - Start all infrastructure services"
    echo "  stop     - Stop all services"
    echo "  restart  - Restart all services"
    echo "  status   - Show status of all services"
    echo "  logs     - Show logs from all services"
    echo "  clean    - Stop services and remove volumes (WARNING: deletes data)"
    echo ""
}

start_services() {
    echo "🚀 Starting infrastructure services..."
    docker-compose up -d
    echo ""
    echo "⏳ Waiting for services to be ready..."
    sleep 10
    echo ""
    docker-compose ps
    echo ""
    echo "✅ Services started! Run './manage_infrastructure.sh status' to check health"
    echo "📊 Ray Dashboard: http://localhost:8265"
}

stop_services() {
    echo "🛑 Stopping infrastructure services..."
    docker-compose down
    echo "✅ Services stopped"
}

restart_services() {
    echo "🔄 Restarting infrastructure services..."
    docker-compose restart
    echo "✅ Services restarted"
}

show_status() {
    echo "📊 Infrastructure Services Status:"
    echo ""
    docker-compose ps
    echo ""
    echo "🔍 Checking service health..."
    
    # Check if services are responding
    if curl -s http://localhost:8265/api/cluster_status > /dev/null 2>&1; then
        echo "✅ Ray dashboard: http://localhost:8265"
    else
        echo "❌ Ray dashboard not responding"
    fi
    
    if docker exec nba-mongodb mongosh --quiet --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        echo "✅ MongoDB is responding"
    else
        echo "❌ MongoDB not responding"
    fi
    
    if docker exec nba-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
        echo "✅ Kafka is responding"
    else
        echo "❌ Kafka not responding"
    fi
}

show_logs() {
    echo "📋 Service Logs (press Ctrl+C to exit):"
    docker-compose logs -f --tail=100
}

clean_services() {
    echo "⚠️  WARNING: This will delete all data in MongoDB and Kafka!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        echo "🗑️  Cleaning up services and volumes..."
        docker-compose down -v
        echo "✅ Cleanup complete"
    else
        echo "❌ Cleanup cancelled"
    fi
}

# Main script logic
case "${1:-}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    clean)
        clean_services
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
