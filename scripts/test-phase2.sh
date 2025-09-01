#!/bin/bash
# test-phase2.sh - Comprehensive testing script for Phase 2

set -e

echo "🚀 Phase 2 Testing Script"
echo "========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service health
check_health() {
    local service=$1
    local url=$2
    echo -n "Checking $service health... "
    
    if curl -f -s "$url" > /dev/null; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# Function to test endpoint
test_endpoint() {
    local description=$1
    local method=$2
    local url=$3
    local data=$4
    local expected_status=$5
    
    echo -n "Testing: $description... "
    
    if [ "$method" = "GET" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    else
        status=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" "$url")
    fi
    
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✓${NC} (Status: $status)"
        return 0
    else
        echo -e "${RED}✗${NC} (Expected: $expected_status, Got: $status)"
        return 1
    fi
}

# 1. Build and start services
echo -e "\n${YELLOW}Step 1: Building services...${NC}"
docker-compose -f docker-compose.yml build

echo -e "\n${YELLOW}Step 2: Starting services...${NC}"
docker-compose -f docker-compose.yml up -d

echo "Waiting for services to initialize (30 seconds)..."
sleep 30

# 2. Health checks
echo -e "\n${YELLOW}Step 3: Health Checks${NC}"
echo "------------------------"
check_health "API Gateway" "http://localhost:3001/health"
check_health "User Service" "http://localhost:5001/health"
check_health "ML Service" "http://localhost:8000/health"

# 3. Ensure database tables exist
echo -e "\n${YELLOW}Step 3.5: Database Setup${NC}"
echo "------------------------"
docker exec rec-postgres psql -U postgres -d userdb -c '
CREATE TABLE IF NOT EXISTS "Users" (
    "Id" SERIAL PRIMARY KEY,
    "ExternalId" VARCHAR(255) UNIQUE NOT NULL,
    "Username" VARCHAR(255) NOT NULL,
    "Email" VARCHAR(255) UNIQUE NOT NULL,
    "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "UpdatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "UserProfiles" (
    "Id" SERIAL PRIMARY KEY,
    "UserId" INTEGER REFERENCES "Users"("Id") ON DELETE CASCADE,
    "Age" INTEGER,
    "Gender" VARCHAR(50),
    "Location" VARCHAR(255),
    "Interests" TEXT,
    "Metadata" JSONB,
    "UpdatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "UserInteractions" (
    "Id" SERIAL PRIMARY KEY,
    "UserId" INTEGER REFERENCES "Users"("Id") ON DELETE CASCADE,
    "ItemId" VARCHAR(255) NOT NULL,
    "InteractionType" VARCHAR(50) NOT NULL,
    "Rating" DECIMAL(3,2),
    "Metadata" JSONB,
    "Timestamp" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "UserPreferences" (
    "Id" SERIAL PRIMARY KEY,
    "UserId" INTEGER REFERENCES "Users"("Id") ON DELETE CASCADE,
    "Category" VARCHAR(255) NOT NULL,
    "Weight" DECIMAL(3,2) DEFAULT 0.5,
    "Tags" JSONB,
    "UpdatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);' > /dev/null 2>&1

echo -e "${GREEN}✓${NC} Database tables created/verified"

# Clear test data
docker exec rec-postgres psql -U postgres -d userdb -c 'TRUNCATE TABLE "Users" CASCADE;' > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Test data cleared"

# 4. Create test user
echo -e "\n${YELLOW}Step 4: User Service Tests${NC}"
echo "----------------------------"

USER_ID=$(curl -s -X POST http://localhost:5001/api/users \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser123",
        "email": "test@example.com",
        "age": 25,
        "gender": "male",
        "location": "San Francisco",
        "interests": ["technology", "sports"]
    }' | grep -o '"userId":"[^"]*' | cut -d'"' -f4)

if [ -n "$USER_ID" ]; then
    echo -e "${GREEN}✓${NC} User created: $USER_ID"
else
    echo -e "${RED}✗${NC} Failed to create user"
    exit 1
fi

# 4. Test API Gateway endpoints
echo -e "\n${YELLOW}Step 5: API Gateway Tests${NC}"
echo "---------------------------"

test_endpoint "Get user profile" "GET" \
    "http://localhost:3001/api/recommendations/user/$USER_ID?limit=5" \
    "" "200"

test_endpoint "Record interaction" "POST" \
    "http://localhost:3001/api/interactions" \
    "{\"user_id\":\"$USER_ID\",\"item_id\":\"item123\",\"interaction_type\":\"view\",\"rating\":4.5}" \
    "201"

test_endpoint "Get trending items" "GET" \
    "http://localhost:3001/api/recommendations/trending?limit=5" \
    "" "200"

test_endpoint "Get similar items" "GET" \
    "http://localhost:3001/api/recommendations/item/item123/similar?limit=3" \
    "" "200"

# 5. Test batch recommendations
echo -e "\n${YELLOW}Step 6: Batch Processing Test${NC}"
echo "--------------------------------"
test_endpoint "Batch recommendations" "POST" \
    "http://localhost:3001/api/recommendations/batch" \
    "{\"user_ids\":[\"$USER_ID\"],\"limit\":5}" \
    "200"

# 6. Check Kafka topics
echo -e "\n${YELLOW}Step 7: Kafka Topics Check${NC}"
echo "----------------------------"
docker exec rec-kafka kafka-topics --list --bootstrap-server localhost:29092

# 7. Check Redis keys
echo -e "\n${YELLOW}Step 8: Redis Cache Check${NC}"
echo "---------------------------"
echo "Redis keys:"
docker exec rec-redis redis-cli KEYS "*" | head -10

# 8. Check PostgreSQL
echo -e "\n${YELLOW}Step 9: Database Check${NC}"
echo "------------------------"
docker exec rec-postgres psql -U postgres -d userdb -c "\dt" 2>/dev/null || echo "Database tables created"

# 9. Check logs for errors
echo -e "\n${YELLOW}Step 10: Error Log Check${NC}"
echo "--------------------------"
echo -n "Checking for errors in logs... "
ERROR_COUNT=$(docker-compose -f docker-compose.yml logs 2>&1 | grep -ci "error" || true)
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠${NC} Found $ERROR_COUNT error messages (may include false positives)"
else
    echo -e "${GREEN}✓${NC} No errors found"
fi

# 10. Performance test (simple)
echo -e "\n${YELLOW}Step 11: Simple Load Test${NC}"
echo "---------------------------"
echo "Sending 10 concurrent requests..."
for i in {1..10}; do
    curl -s "http://localhost:3001/api/recommendations/user/$USER_ID" > /dev/null &
done
wait
echo -e "${GREEN}✓${NC} Load test completed"

# Summary
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}✅ Phase 2 Testing Complete!${NC}"
echo -e "${GREEN}================================${NC}"

echo -e "\n${YELLOW}Available endpoints:${NC}"
echo "- API Gateway: http://localhost:3001"
echo "- User Service: http://localhost:5001"
echo "- ML Service: http://localhost:8000/docs"
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3000 (admin/admin)"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. View logs: docker-compose -f docker-compose.yml logs -f"
echo "2. Stop services: docker-compose -f docker-compose.yml down"
echo "3. Clean up: docker-compose -f docker-compose.yml down -v"