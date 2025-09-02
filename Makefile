# Real-time Recommendation Engine - Makefile
.PHONY: help setup infra-up infra-down dev-up dev-down test-all clean logs

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
	docker-compose up -d ml-service api-gateway user-service kafka-ui redis-commander
	@echo "🌐 Services available at:"
	@echo "  - API Gateway: http://localhost:3000"
	@echo "  - ML Service API: http://localhost:8000"
	@echo "  - User Service API: http://localhost:5000"
	@echo "  - Kafka UI: http://localhost:8080"
	@echo "  - Redis Commander: http://localhost:8081"
	@echo "  - API Documentation:"
	@echo "    - ML Service: http://localhost:8000/docs"
	@echo "    - User Service: http://localhost:5000/swagger"
	@echo "✅ Development environment is ready!"

dev-down: ## Stop development services
	@echo "🛑 Stopping all services..."
	docker-compose down
	@echo "✅ All services stopped"

# Data Management
load-sample-data: ## Generate and load sample data
	@echo "📊 Generating sample data..."
	python3 scripts/generate-sample-data.py
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
	python3 scripts/integration-tests.py
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

build-gateway: ## Build only API Gateway
	@echo "🔨 Building API Gateway..."
	docker-compose build api-gateway
	@echo "✅ API Gateway build complete!"

build-user: ## Build only User service  
	@echo "🔨 Building User service..."
	docker-compose build user-service
	@echo "✅ User service build complete!"

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

# Makefile additions for testing Phase 2

# Quick test commands
.PHONY: test-phase2 test-quick test-health test-cleanup

# Full test suite
test-phase2:
	@chmod +x test-phase2.sh
	@./test-phase2.sh

# Updated Makefile commands with port 3001

# Quick health check only
test-health:
	@echo "Checking service health..."
	@curl -f http://localhost:3001/health || echo "API Gateway not responding"
	@curl -f http://localhost:5001/health || echo "User Service not responding" 
	@curl -f http://localhost:8000/health || echo "ML Service not responding"

# Quick functionality test
test-quick:
	@echo "Quick functionality test..."
	@echo "1. Creating user..."
	@curl -X POST http://localhost:5001/api/users \
		-H "Content-Type: application/json" \
		-d '{"username":"quicktest","email":"quick@test.com","age":30}' | jq '.'
	@echo "\n2. Getting recommendations..."
	@curl http://localhost:3001/api/recommendations/user/quicktest?limit=3 | jq '.'
	@echo "\n3. Recording interaction..."
	@curl -X POST http://localhost:3001/api/interactions \
		-H "Content-Type: application/json" \
		-d '{"user_id":"quicktest","item_id":"test123","interaction_type":"view"}' | jq '.'

phase2-health:
	@echo "Checking API Gateway health..."
	@curl -f http://localhost:3001/health || echo "API Gateway not healthy"
	@echo "\nChecking User Service health..."
	@curl -f http://localhost:5001/health || echo "User Service not healthy"
	@echo "\nChecking ML Service health..."
	@curl -f http://localhost:8000/health || echo "ML Service not healthy"

# Integration test for Phase 2
phase2-integration-test:
	@echo "Creating test user..."
	@curl -X POST http://localhost:5001/api/users \
		-H "Content-Type: application/json" \
		-d '{"username":"testuser","email":"test@example.com","age":25}'
	@echo "\nGetting recommendations..."
	@curl http://localhost:3001/api/recommendations/user/testuser?limit=5
	@echo "\nRecording interaction..."
	@curl -X POST http://localhost:3001/api/interactions \
		-H "Content-Type: application/json" \
		-d '{"user_id":"testuser","item_id":"item123","interaction_type":"view","rating":4.5}'

.PHONY: phase3-up phase3-down phase3-test phase3-build cache-test stream-test ab-test monitoring-up

phase3-build: ## Build Phase 3 services
	@echo "🔨 Building Phase 3 services..."
	docker-compose -f docker-compose.yml -f docker-compose.yml build
	@echo "✅ Phase 3 build complete!"

phase3-up: ## Start Phase 3 services
	@echo "🚀 Starting Phase 3 services..."
	docker-compose -f docker-compose.yml -f docker-compose.yml up -d
	@echo "✅ Phase 3 services started!"

phase3-down: ## Stop Phase 3 services
	@echo "🛑 Stopping Phase 3 services..."
	docker-compose -f docker-compose.yml -f docker-compose.yml down
	@echo "✅ Phase 3 services stopped!"

phase3-test: ## Run Phase 3 tests
	@echo "🧪 Testing Phase 3 components..."
	@chmod +x scripts/test-phase3.sh
	@./scripts/test-phase3.sh

## Individual Service Tests
cache-test: ## Test Rust cache service
	@echo "🧪 Testing cache service..."
	@curl -f http://localhost:8082/health || echo "Cache service not healthy"
	@echo "\nSetting test value..."
	@curl -X PUT "http://localhost:8082/cache/test?ttl=60" \
		-H "Content-Type: application/json" \
		-d '"test_value"' | jq '.'
	@echo "\nGetting test value..."
	@curl http://localhost:8082/cache/test | jq '.'

stream-test: ## Test stream processor
	@echo "🧪 Testing stream processor..."
	@docker logs rec-stream-processor --tail 20

ab-test: ## Test A/B testing framework
	@echo "🧪 Testing A/B framework..."
	@curl -X POST http://localhost:8000/experiments \
		-H "Content-Type: application/json" \
		-d '{"name":"test","allocation":{"control":0.5,"variant":0.5}}' | jq '.'

## Monitoring
monitoring-up: ## Start monitoring stack
	@echo "📊 Starting monitoring..."
	docker-compose -f docker-compose.yml -f docker-compose.yml up -d prometheus grafana
	@echo "📈 Monitoring available at:"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"

monitoring-status: ## Check monitoring status
	@echo "📊 Monitoring Status:"
	@curl -s http://localhost:9090/-/healthy && echo "Prometheus: ✅" || echo "Prometheus: ❌"
	@curl -s http://localhost:3000/api/health && echo "Grafana: ✅" || echo "Grafana: ❌"

cache-stats: ## Get cache statistics
	@echo "📊 Cache Statistics:"
	@curl -s http://localhost:8082/cache/stats | jq '.'

cache-metrics: ## Get cache metrics
	@echo "📊 Cache Metrics:"
	@curl -s http://localhost:8082/metrics | head -50

## Phase 3 Development
phase3-logs: ## View Phase 3 service logs
	@docker-compose -f docker-compose.yml -f docker-compose.yml logs -f cache-service stream-processor

phase3-restart: ## Restart Phase 3 services
	@make phase3-down
	@make phase3-up

phase3-reset: ## Reset Phase 3 with fresh state
	@echo "🔄 Resetting Phase 3..."
	@make phase3-down
	@docker volume prune -f
	@make phase3-build
	@make phase3-up
	@echo "✅ Phase 3 reset complete!"

## Complete stack operations
full-stack-up: ## Start all phases (1, 2, 3)
	@echo "🚀 Starting complete stack..."
	@docker-compose -f docker-compose.yml -f docker-compose.yml up -d
	@echo "✅ All services started!"

full-stack-down: ## Stop all services
	@echo "🛑 Stopping all services..."
	@docker-compose -f docker-compose.yml -f docker-compose.yml down
	@echo "✅ All services stopped!"

full-stack-status: ## Check status of all services
	@echo "📊 Full Stack Status:"
	@docker-compose -f docker-compose.yml -f docker-compose.yml ps