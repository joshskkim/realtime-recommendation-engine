# Deployment Guide

## Prerequisites
- Docker 24.0+
- Docker Compose 2.20+
- Kubernetes 1.27+ (production)
- AWS CLI configured

## Local Development

### Quick Start
```bash
# Clone repository
git clone https://github.com/yourusername/recommendation-engine.git
cd recommendation-engine

# Environment setup
cp .env.example .env
# Edit .env with your configurations

# Start services
docker-compose up -d

# Verify deployment
docker-compose ps
curl http://localhost:3000/health
```

### Service Ports
- API: `http://localhost:3000`
- Kafka UI: `http://localhost:8080`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Grafana: `http://localhost:3001`

## Production Deployment

### AWS ECS Deployment
```bash
# Build and push Docker images
./scripts/build.sh
./scripts/push-to-ecr.sh

# Deploy with Terraform
cd infrastructure/terraform
terraform init
terraform plan
terraform apply

# Update service
aws ecs update-service --cluster prod-cluster \
  --service recommendation-api --force-new-deployment
```

### Kubernetes Deployment
```bash
# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Deploy services
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/

# Verify deployment
kubectl get pods -n recommendation-engine
kubectl get svc -n recommendation-engine
```

### Helm Chart
```bash
# Add repo and install
helm repo add recommendation-engine ./charts
helm install recommendation-engine \
  --namespace production \
  --values values.production.yaml
```

## Environment Variables

```env
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=recommendations
DB_USER=admin
DB_PASSWORD=<secure_password>

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<secure_password>

# Kafka
KAFKA_BROKERS=kafka:9092
KAFKA_TOPIC_EVENTS=user-events

# API
API_PORT=3000
JWT_SECRET=<secure_secret>
NODE_ENV=production
```

## CI/CD Pipeline

### GitHub Actions
```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and test
        run: |
          docker-compose build
          docker-compose run test
      - name: Deploy to production
        run: ./scripts/deploy.sh
```

## Database Migrations

```bash
# Run migrations
npm run migrate:up

# Rollback
npm run migrate:down

# Create new migration
npm run migrate:create add_user_preferences
```

## Monitoring Setup

### Prometheus Configuration
```yaml
scrape_configs:
  - job_name: 'recommendation-api'
    static_configs:
      - targets: ['api:3000']
```

### Grafana Dashboard
Import dashboard ID: `12345` or use `grafana/dashboard.json`

## Backup & Recovery

### Database Backup
```bash
# Manual backup
./scripts/backup-db.sh

# Automated daily backups
0 2 * * * /app/scripts/backup-db.sh
```

### Restore from Backup
```bash
./scripts/restore-db.sh backup-2025-09-03.sql
```

## Scaling Guidelines

### Horizontal Scaling
```bash
# Scale API replicas
kubectl scale deployment api --replicas=5

# Auto-scaling
kubectl autoscale deployment api \
  --min=2 --max=10 --cpu-percent=70
```

### Vertical Scaling
Update resource limits in deployment:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Troubleshooting

### Common Issues

1. **Container fails to start**
```bash
docker-compose logs api
docker exec -it api sh
```

2. **Database connection errors**
```bash
# Check connectivity
docker exec api ping postgres
# Verify credentials
docker exec api env | grep DB_
```

3. **Kafka consumer lag**
```bash
kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group recommendation-consumer --describe
```

## Health Checks

```bash
# API health
curl http://localhost:3000/health

# All services
./scripts/health-check.sh
```

## Rollback Procedure

```bash
# Kubernetes
kubectl rollout undo deployment/api

# Docker Swarm
docker service rollback recommendation-api

# AWS ECS
aws ecs update-service --cluster prod \
  --service api --task-definition api:previous
```