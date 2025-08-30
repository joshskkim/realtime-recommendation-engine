# Real-time Recommendation Engine 🚀

A scalable, real-time recommendation engine built with modern technologies including Kafka Streams, Redis caching, and hybrid ML algorithms. This project demonstrates advanced system design principles, microservices architecture, and polyglot programming.

## 🎯 Project Goals

- **Real-time Processing**: Handle user interactions and generate recommendations in real-time
- **Hybrid Algorithms**: Combine collaborative filtering, content-based, and popularity-based approaches
- **Cold Start Solution**: Effectively handle new users and new items
- **Scalable Architecture**: Microservices design with event-driven communication
- **Technology Showcase**: Demonstrate proficiency in Python, Node.js, C#, Rust, and Kafka

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │   User Service  │    │  Cache Service  │
│    (Node.js)    │    │      (C#)       │    │     (Rust)      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │     ML Service          │
                    │     (FastAPI)           │
                    └────────────┬────────────┘
                                 │
    ┌────────────────────────────┼────────────────────────────┐
    │                            │                            │
┌───▼────┐              ┌──────▼──────┐              ┌──────▼──────┐
│ Kafka  │              │    Redis    │              │ PostgreSQL  │
│Streams │              │   Cache     │              │  Database   │
└────────┘              └─────────────┘              └─────────────┘
```

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **ML Service** | FastAPI + Python | Core recommendation algorithms, model training |
| **API Gateway** | Node.js + Express | Request routing, rate limiting, authentication |
| **User Service** | C# + .NET Core | User management, business logic |
| **Cache Service** | Rust + Redis | High-performance caching layer |
| **Streaming** | Kafka + Kafka Streams | Real-time event processing |
| **Database** | PostgreSQL | Persistent data storage |
| **Cache** | Redis | In-memory caching and session storage |

## ✨ Features

### Core Recommendation Features
- **Collaborative Filtering**: User-based and item-based recommendations
- **Content-Based Filtering**: Feature similarity matching
- **Hybrid Approach**: Intelligent combination of multiple algorithms
- **Real-time Updates**: Live recommendation updates as users interact
- **Cold Start Handling**: Solutions for new users and new items

### System Features
- **High Performance**: Sub-100ms recommendation response times
- **Scalability**: Microservices architecture with horizontal scaling
- **Real-time Processing**: Kafka Streams for live data processing
- **Intelligent Caching**: Multi-layer Redis caching strategy
- **Monitoring**: Built-in metrics and observability

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose (>= 20.x)
- Python (>= 3.9)
- Node.js (>= 16.x)
- Rust (>= 1.60)
- .NET (>= 6.0)
- Git

### 1. Clone and Setup
```bash
git clone https://github.com/YOUR_USERNAME/realtime-recommendation-engine.git
cd realtime-recommendation-engine

# Initial setup
make setup
```

### 2. Configure Environment
```bash
# Edit environment variables
cp .env.example .env
# Update .env with your configuration
```

### 3. Start Development Environment
```bash
# Start all services
make dev-up

# Generate and load sample data
make load-sample-data
```

### 4. Verify Installation
```bash
# Check service health
make health-check

# View service logs
make logs
```

## 🌐 Service URLs

Once running, access the services at:

| Service | URL | Description |
|---------|-----|-------------|
| **ML Service API** | http://localhost:8000 | FastAPI recommendation service |
| **API Documentation** | http://localhost:8000/docs | Interactive API docs |
| **Kafka UI** | http://localhost:8080 | Kafka cluster management |
| **Redis Commander** | http://localhost:8081 | Redis database browser |

## 📊 API Examples

### Get Recommendations
```bash
# Get recommendations for user
curl -X GET "http://localhost:8000/recommendations/user/123?limit=10"

# Get similar items
curl -X GET "http://localhost:8000/recommendations/item/456/similar?limit=5"
```

### Track User Interactions
```bash
# Record user interaction
curl -X POST "http://localhost:8000/interactions" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "item_id": 456, "interaction_type": "view", "rating": 4.5}'
```

### Health Check
```bash
curl http://localhost:8000/health
```

## 🧪 Testing

```bash
# Run all tests
make test-all

# Run ML service tests only
make test-ml

# Run integration tests
make test-integration

# Load testing
make load-test
```

## 🔧 Development Commands

### Common Operations
```bash
make dev-up          # Start development environment
make dev-down        # Stop all services
make dev-restart     # Quick restart
make dev-reset       # Complete reset with fresh data
```

### Debugging
```bash
make logs            # View all service logs
make logs-ml         # View ML service logs only
make shell-ml        # Open ML service shell
make redis-cli       # Open Redis CLI
```

### Data Management
```bash
make load-sample-data    # Generate and load test data
make db-reset           # Reset database
make clean-data         # Clean generated data
```

## 📈 Project Phases

### ✅ Phase 1: Core Infrastructure (Current)
- [x] Docker Compose setup
- [x] Kafka and Redis integration  
- [x] FastAPI ML service with basic CF algorithm
- [x] Sample data generation
- [ ] Basic caching implementation
- [ ] Unit tests and integration tests

### 🔄 Phase 2: Multi-Service Integration (Next)
- [ ] Node.js API Gateway implementation
- [ ] C# User Service development
- [ ] Service-to-service communication
- [ ] Hybrid recommendation logic
- [ ] Authentication and rate limiting

### 🔜 Phase 3: Advanced Features
- [ ] Rust cache service for performance
- [ ] Kafka Streams real-time processing
- [ ] Cold start problem solutions
- [ ] A/B testing framework
- [ ] Advanced monitoring

### 🔜 Phase 4: Production Ready
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline
- [ ] Performance optimization
- [ ] Comprehensive documentation

## 🏗️ Development Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch  
- `feature/*`: Feature development
- `hotfix/*`: Critical fixes

### Commit Convention
```
feat: add collaborative filtering algorithm
fix: resolve Redis connection timeout  
docs: update API documentation
test: add unit tests for recommendation service
chore: update dependencies
```

## 📚 Documentation

- [Architecture Details](docs/architecture.md)
- [API Specifications](docs/api-specs.md)
- [Setup Guide](docs/setup-guide.md)
- [Contributing Guidelines](docs/contributing.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Commit using conventional commits
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for learning and portfolio demonstration
- Inspired by modern recommendation systems at scale
- Thanks to the open-source community for amazing tools

## 📞 Contact

**Your Name**  
📧 your.email@example.com  
🔗 [LinkedIn](https://linkedin.com/in/yourprofile)  
🐙 [GitHub](https://github.com/yourusername)

---

⭐ **Star this repo if you find it useful!** ⭐