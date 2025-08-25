# Makefile for Blocking Responses API

.PHONY: help build start stop test clean logs dev prod monitoring

# Default target
help:
	@echo "Blocking Responses API - Docker Management"
	@echo ""
	@echo "Available commands:"
	@echo "  make start       - Start API and web interface"
	@echo "  make dev         - Start in development mode (with logs)"
	@echo "  make prod        - Start in production mode"
	@echo "  make monitoring  - Start with monitoring (Prometheus + Grafana)"
	@echo "  make test        - Run test suite in container"
	@echo "  make logs        - Show container logs"
	@echo "  make stop        - Stop all services"
	@echo "  make clean       - Clean up containers and volumes"
	@echo "  make build       - Build containers"
	@echo "  make rebuild     - Force rebuild containers"
	@echo "  make shell       - Open shell in API container"
	@echo "  make health      - Check service health"

# Environment setup
.env:
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo "Please edit .env and add your OpenAI API key"; \
	fi

# Build containers
build: .env
	docker-compose build

# Force rebuild
rebuild:
	docker-compose build --no-cache

# Start basic services
start:
	docker-compose up -d backend frontend
	@echo "Services starting at:"
	@echo "  Web Interface: http://localhost"
	@echo "  API: http://localhost:8000"

# Development mode (with logs)
dev:
	docker-compose up backend frontend

# Production mode
prod:
	docker-compose up -d backend frontend
	@make health

# Start with monitoring
monitoring:
	docker-compose --profile monitoring up -d
	@echo "Services available at:"
	@echo "  Web Interface: http://localhost"
	@echo "  API: http://localhost:8000"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana: http://localhost:3000"

# Run tests
test:
	docker-compose build backend
	docker-compose run --rm backend pytest tests/ -v

# Run tests with coverage
test-coverage:
	docker-compose build backend
	docker-compose run --rm backend pytest tests/ --cov=app --cov-report=html

# Show logs
logs:
	docker-compose logs -f

# Stop services
stop:
	docker-compose --profile monitoring --profile redis down

# Clean up everything
clean:
	docker-compose --profile monitoring --profile redis down -v --remove-orphans
	docker system prune -f

# Deep clean (including images)
clean-all:
	docker-compose --profile monitoring --profile redis down -v --remove-orphans --rmi all
	docker system prune -af --volumes

# Open shell in backend container
shell:
	docker-compose exec backend /bin/bash

# Check health
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health 2>/dev/null && echo "✓ API is healthy" || echo "✗ API is not responding"
	@curl -f http://localhost/nginx-health 2>/dev/null && echo "✓ Web interface is healthy" || echo "✗ Web interface is not responding"

# Show status
status:
	docker-compose ps

# Update containers (pull latest images)
update:
	docker-compose pull
	docker-compose up -d

# Backup data (if using volumes)
backup:
	@mkdir -p backups
	@echo "Backing up Redis data..."
	docker run --rm -v blocking-responses-poc_redis_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/redis-$(shell date +%Y%m%d-%H%M%S).tar.gz -C /data .
	@echo "Backing up Prometheus data..."
	docker run --rm -v blocking-responses-poc_prometheus_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/prometheus-$(shell date +%Y%m%d-%H%M%S).tar.gz -C /data .

.PHONY: help build start dev prod monitoring test test-coverage logs stop clean health shell rebuild backup