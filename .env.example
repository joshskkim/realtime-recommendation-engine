# Real-time Recommendation Engine - Makefile
.PHONY: help setup infra-up infra-down dev-up dev-down test-all clean logs

# Default target
help: ## Show this help message
	@echo "Real-time Recommendation Engine - Development Commands"
	@echo "=====================================================\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Environment Setup
setup: ## Initial project setup (copy env files, install dependencies)
	@echo "🚀 Setting up development environment..."
	cp .env.example .env || echo ".env already exists"
	chmod +x scripts/setup-env.sh
	chmod +x scripts/generate-sample-data.py
	chmod +x infrastructure/kafka/topics-setup.sh
	@echo "✅ Setup complete! Edit .env file with your configuration."

# Infrastructure Management
infra-up: ## Start core infrastructure (Kafka, Redis, PostgreSQL)
	@echo "🏗️  Starting infrastructure services..."
	docker-compose up -d zookeeper kafka redis postgres
	@echo "⏳ Waiting for services to be healthy..."
	@sleep 10
	@echo "📊 Creating Kafka topics..."
	./infrastructure/kafka/topics-setup.sh
	@echo "✅ Infrastructure is ready!"

infra-down: ## Stop infrastructure services
	@echo "🛑 Stopping infrastructure services..."
	docker-compose down
	@echo "✅ Infrastructure stopped"

# Development Environment
dev-up: infra-up ## Start all services in development mode
	@echo "🔧 Starting development services..."
	docker-compose up -d ml-service kafka-ui redis-commander
	@echo "🌐 Services available at:"
	@echo "  - ML Service API: http://localhost:8000"
	@echo "  - Kafka UI: http://localhost:8080"
	@echo "  - Redis Commander: http://localhost:8081"
	@echo "  - API Documentation: http://localhost:8000/docs"
	@echo "✅ Development environment is ready!"

dev-down: ## Stop development services
	@echo "🛑 Stopping all services..."
	docker-compose down
	@echo "✅ All services stopped"

# Data Management
load-sample-data: ## Generate and load sample data
	@echo "📊 Generating sample data..."
	python scripts/generate-sample-data.py
	@echo "📥 Loading data into services..."
	./scripts/load-test-data.sh
	@echo "✅ Sample data loaded successfully!"

# Testing
test-all: ## Run tests across all services
	@echo "🧪 Running all tests..."
	@echo "Testing ML Service..."
	docker-compose exec ml-service python -m pytest tests/ -v
	@echo "✅ All tests completed!"

test-ml: ## Run ML service tests only
	@echo "🧪 Testing ML Service..."
	docker-compose exec ml-service python -m pytest tests/ -v

test-integration: ## Run integration tests
	@echo "🧪 Running integration tests..."
	python scripts/integration-tests.py
	@echo "✅ Integration tests completed!"

# Monitoring and Debugging
logs: ## Show logs for all services
	docker-compose logs -f

logs-ml: ## Show ML service logs
	docker-compose logs -f ml-service

logs-kafka: ## Show Kafka logs
	docker-compose logs -f kafka

health-check: ## Check health of all services
	@echo "🏥 Checking service health..."
	@curl -s http://localhost:8000/health | jq . || echo "ML Service not responding"
	@docker-compose ps
	@echo "✅ Health check completed!"

# Database Operations
db-reset: ## Reset PostgreSQL database
	@echo "🗃️  Resetting database..."
	docker-compose exec postgres psql -U recuser -d recommendations -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"
	docker-compose restart ml-service
	@echo "✅ Database reset complete!"

# Cleanup
clean: ## Clean up containers, volumes, and generated data
	@echo "🧹 Cleaning up..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	rm -rf datasets/generated/
	@echo "✅ Cleanup complete!"

clean-data: ## Clean up only generated data
	@echo "🧹 Cleaning up generated data..."
	rm -rf datasets/generated/
	@echo "✅ Data cleanup complete!"

# Development Utilities
shell-ml: ## Open shell in ML service container
	docker-compose exec ml-service bash

shell-kafka: ## Open Kafka shell for debugging
	docker-compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic user-interactions --from-beginning

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

# Build Operations
build: ## Build all Docker images
	@echo "🔨 Building Docker images..."
	docker-compose build
	@echo "✅ Build complete!"

build-ml: ## Build only ML service
	@echo "🔨 Building ML service..."
	docker-compose build ml-service
	@echo "✅ ML service build complete!"

# Performance Testing
load-test: ## Run basic load tests
	@echo "⚡ Running load tests..."
	python scripts/load-test.py
	@echo "✅ Load tests completed!"

# Git Helpers
git-setup: ## Set up git hooks and aliases
	@echo "🔧 Setting up git configuration..."
	git config --local commit.template .gitmessage
	@echo "✅ Git setup complete!"

# Documentation
docs-serve: ## Serve documentation locally
	@echo "📚 Starting documentation server..."
	cd docs && python -m http.server 8082
	@echo "📖 Documentation available at http://localhost:8082"

# Production Simulation
prod-sim: ## Run production-like environment
	@echo "🏭 Starting production simulation..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "✅ Production simulation started!"

# Monitoring
monitor: ## Start monitoring stack (Prometheus, Grafana)
	@echo "📊 Starting monitoring stack..."
	docker-compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d
	@echo "📈 Monitoring available at:"
	@echo "  - Grafana: http://localhost:3000"
	@echo "  - Prometheus: http://localhost:9090"

# Quick development workflow
dev-restart: dev-down dev-up ## Quick restart of development environment

dev-reset: clean setup dev-up load-sample-data ## Complete development reset

# Status check
status: ## Show status of all services
	@echo "📊 Service Status:"
	@echo "=================="
	@docker-compose ps
	@echo "\n🌐 Service URLs:"
	@echo "=================="
	@echo "ML Service API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Kafka UI: http://localhost:8080"  
	@echo "Redis Commander: http://localhost:8081"