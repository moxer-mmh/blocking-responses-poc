#!/bin/bash

# Docker run script for Blocking Responses API
# Usage: ./docker-run.sh [mode] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
MODE=${1:-"basic"}
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

print_usage() {
    echo "Usage: $0 [mode] [options]"
    echo ""
    echo "Modes:"
    echo "  basic      - Start API and web interface only (default)"
    echo "  redis      - Start with Redis for shared metrics"
    echo "  monitoring - Start with full monitoring stack (Prometheus + Grafana)"
    echo "  dev        - Development mode with volume mounts"
    echo "  prod       - Production mode without dev mounts"
    echo "  test       - Run tests in container"
    echo "  logs       - Show logs from running containers"
    echo "  stop       - Stop all services"
    echo "  clean      - Stop and remove all containers, volumes, and networks"
    echo ""
    echo "Options:"
    echo "  --build    - Force rebuild of images"
    echo "  --detach   - Run in background (default for most modes)"
    echo "  --help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 basic              # Start basic API + web interface"
    echo "  $0 monitoring --build # Start with monitoring, rebuild images"
    echo "  $0 dev                # Start in development mode"
    echo "  $0 test               # Run test suite"
    echo "  $0 clean              # Clean up everything"
}

check_requirements() {
    # Check if docker and docker-compose are available
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is not installed${NC}"
        exit 1
    fi
    
    # Use 'docker compose' if available, otherwise 'docker-compose'
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi
}

check_env() {
    if [[ ! -f "$ENV_FILE" ]]; then
        echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example${NC}"
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            echo -e "${YELLOW}Please edit .env file and add your OpenAI API key${NC}"
        else
            echo -e "${RED}Error: .env.example file not found${NC}"
            exit 1
        fi
    fi
    
    # Check if OpenAI API key is set
    if ! grep -q "OPENAI_API_KEY=.*[^[:space:]]" "$ENV_FILE" 2>/dev/null; then
        echo -e "${YELLOW}Warning: OpenAI API key may not be set in .env file${NC}"
        echo -e "${YELLOW}The API will not work without a valid OpenAI API key${NC}"
    fi
}

start_basic() {
    echo -e "${GREEN}Starting Blocking Responses API (basic mode)${NC}"
    $DOCKER_COMPOSE up -d api web
    show_access_info
}

start_redis() {
    echo -e "${GREEN}Starting with Redis support${NC}"
    $DOCKER_COMPOSE --profile redis up -d
    show_access_info
}

start_monitoring() {
    echo -e "${GREEN}Starting with full monitoring stack${NC}"
    $DOCKER_COMPOSE --profile monitoring up -d
    show_access_info
    echo -e "${BLUE}Monitoring services:${NC}"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana:    http://localhost:3000 (admin/admin123)"
}

start_dev() {
    echo -e "${GREEN}Starting in development mode${NC}"
    # Ensure volume mounts are enabled in docker-compose.yml
    $DOCKER_COMPOSE up api web
}

start_prod() {
    echo -e "${GREEN}Starting in production mode${NC}"
    # Remove volume mounts for production
    $DOCKER_COMPOSE -f docker-compose.prod.yml up -d 2>/dev/null || {
        echo -e "${YELLOW}No production compose file found, using main file${NC}"
        $DOCKER_COMPOSE up -d api web
    }
    show_access_info
}

run_tests() {
    echo -e "${GREEN}Running test suite in container${NC}"
    $DOCKER_COMPOSE build api
    $DOCKER_COMPOSE run --rm backend pytest backend/tests/ -v
}

show_logs() {
    echo -e "${GREEN}Showing logs from running containers${NC}"
    $DOCKER_COMPOSE logs -f
}

stop_services() {
    echo -e "${YELLOW}Stopping all services${NC}"
    $DOCKER_COMPOSE --profile redis --profile monitoring down
}

clean_all() {
    echo -e "${YELLOW}Cleaning up all containers, volumes, and networks${NC}"
    $DOCKER_COMPOSE --profile redis --profile monitoring down -v --remove-orphans
    docker system prune -f --volumes
    echo -e "${GREEN}Cleanup complete${NC}"
}

show_access_info() {
    echo -e "${GREEN}Services are starting up...${NC}"
    echo -e "${BLUE}Access your services at:${NC}"
    echo "  Web Interface: http://localhost"
    echo "  API Direct:    http://localhost:8000"
    echo "  API Docs:      http://localhost:8000/docs"
    echo "  Health Check:  http://localhost:8000/health"
    echo ""
    echo -e "${BLUE}Wait for services to be healthy, then test with:${NC}"
    echo "  curl http://localhost:8000/health"
    echo "  docker-compose logs -f api"
}

wait_for_services() {
    echo -e "${BLUE}Waiting for services to be healthy...${NC}"
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Services are healthy and ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}✗ Services failed to become healthy within timeout${NC}"
    echo "Check logs with: docker-compose logs api"
    return 1
}

# Parse arguments
BUILD_FLAG=""
DETACH_MODE="true"

for arg in "$@"; do
    case $arg in
        --build)
            BUILD_FLAG="--build"
            ;;
        --detach)
            DETACH_MODE="true"
            ;;
        --no-detach)
            DETACH_MODE="false"
            ;;
        --help)
            print_usage
            exit 0
            ;;
    esac
done

# Add build flag if specified
if [[ -n "$BUILD_FLAG" ]]; then
    export COMPOSE_HTTP_TIMEOUT=300  # Increase timeout for builds
fi

# Main execution
check_requirements
check_env

case $MODE in
    "basic"|"")
        start_basic
        ;;
    "redis")
        start_redis
        ;;
    "monitoring")
        start_monitoring
        ;;
    "dev")
        DETACH_MODE="false"
        start_dev
        ;;
    "prod")
        start_prod
        ;;
    "test")
        run_tests
        ;;
    "logs")
        show_logs
        ;;
    "stop")
        stop_services
        ;;
    "clean")
        clean_all
        ;;
    *)
        echo -e "${RED}Error: Unknown mode '$MODE'${NC}"
        print_usage
        exit 1
        ;;
esac