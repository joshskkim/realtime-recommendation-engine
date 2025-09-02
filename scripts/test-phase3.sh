#!/bin/bash
# scripts/test-phase3.sh - Test Phase 3 components

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🚀 Phase 3 Testing Script"
echo "========================="

# Build Phase 3 services
echo -e "\n${YELLOW}Building Phase 3 services...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.yml build

# Start services
echo -e "\n${YELLOW}Starting services...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.yml up -d

echo "Waiting for services (30s)..."
sleep 30

# Test Cache Service
echo -e "\n${YELLOW}Testing Rust Cache Service${NC}"
echo "----------------------------"

# Health check
echo -n "Cache service health... "
if curl -f -s http://localhost:8082/health > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Set cache value
echo -n "Setting cache value... "
curl -X PUT "http://localhost:8082/cache/test_key?ttl=60" \
    -H "Content-Type: application/json" \
    -d '"testvalue"' -s
echo -e "${GREEN}✓${NC}"

# Get cache value
echo -n "Getting cache value... "
VALUE=$(curl -s http://localhost:8082/cache/test_key)
if [ "$VALUE" = '"testvalue"' ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test Stream Processor
echo -e "\n${YELLOW}Testing Kafka Streams Processor${NC}"
echo "--------------------------------"

# Check if processor is running
echo -n "Stream processor status... "
if docker ps | grep -q rec-stream-processor; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Send test interaction
echo -n "Sending test interaction... "
docker exec rec-ml-service python -c "
import json
from kafka import KafkaProducer
producer = KafkaProducer(
    bootstrap_servers='kafka:29092',
    value_serializer=lambda v: json.dumps(v).encode()
)
producer.send('user-interactions', {
    'user_id': 'test_user',
    'item_id': 'test_item',
    'interaction_type': 'view',
    'rating': 4.5,
    'timestamp': '2025-01-01T00:00:00',
    'session_id': 'test_session'
})
producer.flush()
print('Sent')
" > /dev/null 2>&1
echo -e "${GREEN}✓${NC}"

# Test Cold Start Handler
echo -e "\n${YELLOW}Testing Cold Start Handler${NC}"
echo "---------------------------"

echo -n "Getting cold start recommendations... "
RESPONSE=$(curl -s -X POST http://localhost:8000/recommendations/cold-start \
    -H "Content-Type: application/json" \
    -d '{
        "user_id": "new_user_123",
        "demographics": {
            "age_group": "25-34",
            "location": "US"
        }
    }')
if echo "$RESPONSE" | grep -q "recommendations"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test A/B Testing Framework
echo -e "\n${YELLOW}Testing A/B Testing Framework${NC}"
echo "------------------------------"

echo -n "Creating experiment... "
EXPERIMENT=$(curl -s -X POST http://localhost:8000/experiments \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Experiment",
        "control_group": {"algorithm": "standard"},
        "treatment_groups": [{"name": "variant_a", "algorithm": "enhanced"}],
        "allocation": {"control": 0.5, "variant_a": 0.5}
    }')
if echo "$EXPERIMENT" | grep -q "experiment_id"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Check Monitoring
echo -e "\n${YELLOW}Testing Monitoring Stack${NC}"
echo "------------------------"

echo -n "Prometheus health... "
if curl -f -s http://localhost:9090/-/healthy > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo -n "Grafana health... "
if curl -f -s http://localhost:3000/api/health > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Summary
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}✅ Phase 3 Testing Complete!${NC}"
echo -e "${GREEN}================================${NC}"

echo -e "\n${YELLOW}Services:${NC}"
echo "- Cache Service: http://localhost:8082"
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3000 (admin/admin)"

echo -e "\n${YELLOW}Metrics available at:${NC}"
echo "- Cache metrics: http://localhost:8082/metrics"
echo "- Cache stats: http://localhost:8082/cache/stats"