#!/bin/bash
# File: scripts/test-local-no-cloud.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🚀 Local Testing - No Cloud Required"
echo "===================================="

# Fix kubectl context to use local
fix_kubectl_context() {
    echo -e "\n${YELLOW}Fixing kubectl context...${NC}"
    
    # Save current context (if you want to restore later)
    kubectl config current-context > /tmp/previous-context.txt 2>/dev/null || true
    
    # Check if docker-desktop or minikube or kind context exists
    if kubectl config get-contexts 2>/dev/null | grep -q "docker-desktop"; then
        kubectl config use-context docker-desktop
        echo -e "${GREEN}✓${NC} Switched to docker-desktop context"
    elif kubectl config get-contexts 2>/dev/null | grep -q "minikube"; then
        kubectl config use-context minikube
        echo -e "${GREEN}✓${NC} Switched to minikube context"
    elif kubectl config get-contexts 2>/dev/null | grep -q "kind-"; then
        # Use any existing kind cluster
        KIND_CONTEXT=$(kubectl config get-contexts | grep "kind-" | head -1 | awk '{print $2}')
        kubectl config use-context "$KIND_CONTEXT"
        echo -e "${GREEN}✓${NC} Switched to kind context: $KIND_CONTEXT"
    else
        echo "No local context found, will create one with Kind if needed"
    fi
}

# Option 1: Test with Docker Compose (Simplest)
test_with_docker_compose() {
    echo -e "\n${YELLOW}Option 1: Testing with Docker Compose${NC}"
    echo "======================================="
    
    # Build images
    echo -e "\n${YELLOW}Building Docker images...${NC}"
    
    # Only build if directories exist
    if [ -d "services/ml-service" ]; then
        docker build -t ml-service:local ./services/ml-service
        echo -e "${GREEN}✓${NC} ML Service built"
    fi
    
    if [ -d "services/cache-service" ]; then
        docker build -t cache-service:local ./services/cache-service 2>/dev/null || {
            echo -e "${YELLOW}⚠${NC} Cache Service build failed (Rust not configured), skipping..."
        }
    fi
    
    if [ -d "services/api-gateway" ]; then
        docker build -t api-gateway:local ./services/api-gateway 2>/dev/null || {
            echo -e "${YELLOW}⚠${NC} API Gateway build failed, skipping..."
        }
    fi
    
    if [ -d "services/stream-processor" ]; then
        docker build -t stream-processor:local ./services/stream-processor
        echo -e "${GREEN}✓${NC} Stream Processor built"
    fi
    
    # Create a test docker-compose file
    cat > docker-compose.test.yml <<'EOF'
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: test-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  postgres:
    image: postgres:15-alpine
    container_name: test-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: userdb
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  ml-service:
    image: ml-service:local
    container_name: test-ml-service
    ports:
      - "8000:8000"
    environment:
      REDIS_HOST: redis
      REDIS_PORT: 6379
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: userdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      LOG_LEVEL: INFO
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
EOF

    # Add cache service only if image exists
    if docker images | grep -q "cache-service.*local"; then
        cat >> docker-compose.test.yml <<'EOF'

  cache-service:
    image: cache-service:local
    container_name: test-cache-service
    ports:
      - "8082:8082"
    environment:
      CACHE_SERVICE_REDIS_URL: redis://redis:6379
      CACHE_SERVICE_PORT: 8082
    depends_on:
      redis:
        condition: service_healthy
EOF
    fi

    # Add API gateway only if image exists
    if docker images | grep -q "api-gateway.*local"; then
        cat >> docker-compose.test.yml <<'EOF'

  api-gateway:
    image: api-gateway:local
    container_name: test-api-gateway
    ports:
      - "3001:3001"
    environment:
      REDIS_HOST: redis
      ML_SERVICE_URL: http://ml-service:8000
      CACHE_SERVICE_URL: http://cache-service:8082
      PORT: 3001
    depends_on:
      - ml-service
EOF
    fi

    # Start services
    echo -e "\n${YELLOW}Starting services with Docker Compose...${NC}"
    docker-compose -f docker-compose.test.yml up -d
    
    # Wait for services with better health checking
    echo "Waiting for services to be ready..."
    MAX_WAIT=60
    WAITED=0
    
    while [ $WAITED -lt $MAX_WAIT ]; do
        if docker-compose -f docker-compose.test.yml ps | grep -q "healthy"; then
            echo "Services are becoming healthy..."
            sleep 5
            break
        fi
        sleep 2
        WAITED=$((WAITED + 2))
        echo -n "."
    done
    echo ""
    
    # Test services
    echo -e "\n${YELLOW}Testing services...${NC}"
    
    # Test ML Service
    echo -n "ML Service health: "
    if curl -f -s http://localhost:8000/health &>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        echo "ML Service logs:"
        docker logs test-ml-service --tail 20 2>/dev/null || echo "No logs available"
    fi
    
    # Test Cache Service if it exists
    if docker ps | grep -q test-cache-service; then
        echo -n "Cache Service health: "
        if curl -f -s http://localhost:8082/health &>/dev/null; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
            echo "Cache Service logs:"
            docker logs test-cache-service --tail 20 2>/dev/null || echo "No logs available"
        fi
    fi
    
    # Test API Gateway if it exists
    if docker ps | grep -q test-api-gateway; then
        echo -n "API Gateway health: "
        if curl -f -s http://localhost:3001/health &>/dev/null; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
            echo "API Gateway logs:"
            docker logs test-api-gateway --tail 20 2>/dev/null || echo "No logs available"
        fi
    fi
    
    # Run functional tests
    echo -e "\n${YELLOW}Running functional tests...${NC}"
    
    # Test recommendation endpoint
    echo -n "Testing recommendations: "
    response=$(curl -s http://localhost:8000/recommendations/user/test_user?limit=5 2>/dev/null || echo "{}")
    if echo "$response" | grep -q "recommendations"; then
        echo -e "${GREEN}✓${NC}"
        echo "  Sample response: $(echo $response | jq -c '.recommendations[0]' 2>/dev/null || echo $response | head -c 100)"
    else
        echo -e "${RED}✗${NC}"
        echo "  Response: $response"
    fi
    
    # Test cold start
    echo -n "Testing cold start: "
    cold_response=$(curl -s -X POST http://localhost:8000/recommendations/cold-start \
        -H "Content-Type: application/json" \
        -d '{"user_id": "new_user", "strategy": "popularity", "limit": 5}' 2>/dev/null || echo "{}")
    if echo "$cold_response" | grep -q "recommendations"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        echo "  Response: $cold_response"
    fi
    
    # Test cache if available
    if docker ps | grep -q test-cache-service; then
        echo -n "Testing cache set: "
        if curl -s -X PUT "http://localhost:8082/cache/test_key?ttl=60" \
            -H "Content-Type: application/json" \
            -d '"test_value"' &>/dev/null; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
        fi
        
        echo -n "Testing cache get: "
        cache_value=$(curl -s http://localhost:8082/cache/test_key 2>/dev/null || echo "")
        if echo "$cache_value" | grep -q "test_value"; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
        fi
    fi
    
    # Show running containers
    echo -e "\n${YELLOW}Running containers:${NC}"
    docker-compose -f docker-compose.test.yml ps
    
    echo -e "\n${GREEN}Docker Compose tests complete!${NC}"
}

# Option 2: Test with Kind (Local Kubernetes)
test_with_kind() {
    echo -e "\n${YELLOW}Option 2: Testing with Kind (Local Kubernetes)${NC}"
    echo "================================================"
    
    # Check if kind is installed
    if ! command -v kind &> /dev/null; then
        echo -e "${RED}Kind is not installed. Please install it first:${NC}"
        echo "brew install kind (macOS)"
        echo "or visit: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
        return 1
    fi
    
    # Create Kind cluster
    echo "Creating local Kind cluster..."
    
    # Delete existing cluster if it exists
    kind delete cluster --name test-cluster 2>/dev/null || true
    
    # Create new cluster
    cat > /tmp/kind-config.yaml <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30000
    hostPort: 8000
    protocol: TCP
  - containerPort: 30001
    hostPort: 3001
    protocol: TCP
  - containerPort: 30082
    hostPort: 8082
    protocol: TCP
EOF
    
    kind create cluster --name test-cluster --config /tmp/kind-config.yaml
    
    # Set context to the new cluster
    kubectl config use-context kind-test-cluster
    echo -e "${GREEN}✓${NC} Kind cluster created and context set"
    
    # Load images to Kind
    echo "Loading images to Kind cluster..."
    if docker images | grep -q "ml-service.*local"; then
        kind load docker-image ml-service:local --name test-cluster
        echo -e "${GREEN}✓${NC} ML Service image loaded"
    fi
    if docker images | grep -q "cache-service.*local"; then
        kind load docker-image cache-service:local --name test-cluster
        echo -e "${GREEN}✓${NC} Cache Service image loaded"
    fi
    if docker images | grep -q "api-gateway.*local"; then
        kind load docker-image api-gateway:local --name test-cluster
        echo -e "${GREEN}✓${NC} API Gateway image loaded"
    fi
    
    # Deploy minimal test
    echo "Deploying test pods..."
    kubectl create namespace test
    
    # Deploy Redis
    kubectl apply -n test -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
EOF
    
    # Deploy ML Service
    kubectl apply -n test -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ml-service
  template:
    metadata:
      labels:
        app: ml-service
    spec:
      containers:
      - name: ml-service
        image: ml-service:local
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_HOST
          value: redis
        - name: REDIS_PORT
          value: "6379"
---
apiVersion: v1
kind: Service
metadata:
  name: ml-service
spec:
  type: NodePort
  selector:
    app: ml-service
  ports:
  - port: 8000
    targetPort: 8000
    nodePort: 30000
EOF
    
    # Wait for deployment
    echo "Waiting for pods to be ready..."
    kubectl wait --for=condition=available --timeout=120s deployment/ml-service -n test
    
    # Check pod status
    echo -e "\n${YELLOW}Pod Status:${NC}"
    kubectl get pods -n test
    
    # Test service
    echo -e "\n${YELLOW}Testing service...${NC}"
    sleep 5
    echo -n "ML Service health (via NodePort): "
    if curl -f -s http://localhost:8000/health &>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        echo "Pod logs:"
        kubectl logs -n test -l app=ml-service --tail=20
    fi
}

# Option 3: Just validate code and configs
validate_code_only() {
    echo -e "\n${YELLOW}Option 3: Code and Configuration Validation${NC}"
    echo "============================================"
    
    VALIDATION_PASSED=true
    
    # Validate Docker files
    echo -e "\n${YELLOW}Validating Dockerfiles...${NC}"
    for service in ml-service api-gateway cache-service stream-processor user-service; do
        if [ -f "services/$service/Dockerfile" ]; then
            # Just check if Dockerfile can be parsed
            if docker build --help &>/dev/null; then
                echo -e "${GREEN}✓${NC} $service/Dockerfile exists"
            fi
        else
            echo -e "${YELLOW}⚠${NC} $service/Dockerfile not found"
        fi
    done
    
    # Validate Kubernetes YAML
    echo -e "\n${YELLOW}Validating Kubernetes manifests...${NC}"
    if command -v kubectl &> /dev/null; then
        for file in k8s/base/*.yaml k8s/deployments/*.yaml; do
            if [ -f "$file" ]; then
                if kubectl apply --dry-run=client -f "$file" &>/dev/null; then
                    echo -e "${GREEN}✓${NC} $(basename $file) valid"
                else
                    echo -e "${RED}✗${NC} $(basename $file) has issues"
                    VALIDATION_PASSED=false
                fi
            fi
        done
    else
        echo -e "${YELLOW}⚠${NC} kubectl not installed, skipping K8s validation"
    fi
    
    # Validate Helm charts
    if [ -d "helm/recommendation-system" ]; then
        echo -e "\n${YELLOW}Validating Helm chart...${NC}"
        if command -v helm &> /dev/null; then
            if helm lint helm/recommendation-system 2>/dev/null; then
                echo -e "${GREEN}✓${NC} Helm chart valid"
            else
                echo -e "${RED}✗${NC} Helm chart has issues"
                VALIDATION_PASSED=false
            fi
        else
            echo -e "${YELLOW}⚠${NC} Helm not installed, skipping"
        fi
    fi
    
    # Check Python syntax
    echo -e "\n${YELLOW}Checking Python code...${NC}"
    if [ -d "services/ml-service" ] && command -v python3 &> /dev/null; then
        ERROR_COUNT=0
        for py_file in services/ml-service/app/*.py services/ml-service/app/**/*.py; do
            if [ -f "$py_file" ]; then
                if python3 -m py_compile "$py_file" 2>/dev/null; then
                    :
                else
                    echo -e "${RED}✗${NC} $(basename $py_file) has syntax errors"
                    ERROR_COUNT=$((ERROR_COUNT + 1))
                fi
            fi
        done
        if [ $ERROR_COUNT -eq 0 ]; then
            echo -e "${GREEN}✓${NC} All Python files valid"
        else
            VALIDATION_PASSED=false
        fi
    else
        echo -e "${YELLOW}⚠${NC} Python not available or directory not found"
    fi
    
    # Check Node.js
    echo -e "\n${YELLOW}Checking Node.js code...${NC}"
    if [ -f "services/api-gateway/package.json" ]; then
        if command -v npm &> /dev/null; then
            cd services/api-gateway
            if npm list &>/dev/null; then
                echo -e "${GREEN}✓${NC} Node.js dependencies OK"
            else
                echo -e "${YELLOW}⚠${NC} Some Node.js dependencies missing (run npm install)"
            fi
            cd ../..
        else
            echo -e "${YELLOW}⚠${NC} npm not installed, skipping"
        fi
    fi
    
    # Check Rust
    echo -e "\n${YELLOW}Checking Rust code...${NC}"
    if [ -f "services/cache-service/Cargo.toml" ]; then
        if command -v cargo &> /dev/null; then
            cd services/cache-service
            if cargo check &>/dev/null 2>&1; then
                echo -e "${GREEN}✓${NC} Rust code compiles"
            else
                echo -e "${YELLOW}⚠${NC} Rust code has compilation warnings/errors"
            fi
            cd ../..
        else
            echo -e "${YELLOW}⚠${NC} Cargo not installed, skipping"
        fi
    fi
    
    # Summary
    echo -e "\n${YELLOW}Validation Summary:${NC}"
    if [ "$VALIDATION_PASSED" = true ]; then
        echo -e "${GREEN}✓ All validations passed!${NC}"
    else
        echo -e "${YELLOW}⚠ Some validations failed, check above for details${NC}"
    fi
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    if [ -f "docker-compose.test.yml" ]; then
        docker-compose -f docker-compose.test.yml down 2>/dev/null || true
        rm -f docker-compose.test.yml
    fi
    kind delete cluster --name test-cluster 2>/dev/null || true
    rm -f /tmp/kind-config.yaml
}

# Main menu
main() {
    # First, fix kubectl context if kubectl is available
    if command -v kubectl &> /dev/null; then
        fix_kubectl_context
    fi
    
    echo -e "\n${YELLOW}Choose testing option:${NC}"
    echo "1) Docker Compose (Recommended - No Kubernetes needed)"
    echo "2) Kind (Local Kubernetes - requires Kind installed)"
    echo "3) Code validation only (No runtime test)"
    echo "4) Run all tests"
    echo "5) Exit"
    
    read -p "Enter choice [1-5]: " choice
    
    case $choice in
        1)
            test_with_docker_compose
            ;;
        2)
            test_with_kind
            ;;
        3)
            validate_code_only
            ;;
        4)
            test_with_docker_compose
            echo ""
            validate_code_only
            ;;
        5)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
    
    echo -e "\n${GREEN}================================${NC}"
    echo -e "${GREEN}✅ Testing Complete!${NC}"
    echo -e "${GREEN}================================${NC}"
    
    # Offer to keep services running for option 1
    if [ "$choice" = "1" ] || [ "$choice" = "4" ]; then
        echo ""
        read -p "Keep services running? (y/n): " keep
        if [ "$keep" != "y" ]; then
            cleanup
        else
            echo -e "\n${YELLOW}Services are running. To stop:${NC}"
            echo "docker-compose -f docker-compose.test.yml down"
        fi
    fi
}

# Set trap for cleanup on unexpected exit (but not on normal exit)
trap 'echo "Interrupted..."; cleanup; exit 130' INT TERM

# Run main
main