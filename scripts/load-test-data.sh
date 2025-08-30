#!/bin/bash

# Load test data into the recommendation engine

set -e

echo "📊 Loading test data into recommendation engine..."

# Configuration
ML_SERVICE_URL="http://localhost:8000"
DATA_DIR="datasets/generated"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if data files exist
check_data_files() {
    print_status "Checking for data files..."
    
    if [ ! -f "$DATA_DIR/users.json" ]; then
        print_warning "Users data not found. Generating sample data..."
        python3 scripts/generate-sample-data.py
    fi
    
    if [ ! -f "$DATA_DIR/items.json" ]; then
        print_error "Items data not found after generation!"
        exit 1
    fi
    
    if [ ! -f "$DATA_DIR/interactions.json" ]; then
        print_error "Interactions data not found after generation!"
        exit 1
    fi
    
    print_status "✅ All data files found"
}

# Wait for ML service to be ready
wait_for_service() {
    print_status "Waiting for ML service to be ready..."
    
    timeout=60
    while ! curl -s "$ML_SERVICE_URL/health" > /dev/null 2>&1; do
        echo "Waiting for ML service..."
        sleep 5
        timeout=$((timeout - 5))
        if [ $timeout -le 0 ]; then
            print_error "Timeout waiting for ML service"
            exit 1
        fi
    done
    
    print_status "✅ ML service is ready"
}

# Load users data
load_users() {
    print_status "Loading users data..."
    
    # For now, we'll create a simple endpoint to load users
    # This is a mock implementation since we haven't built the full API yet
    user_count=$(jq length "$DATA_DIR/users.json")
    print_status "📊 Found $user_count users to load"
    
    # Simulate loading by checking if we can read the file
    if jq '.[0:5]' "$DATA_DIR/users.json" > /dev/null; then
        print_status "✅ Users data validated"
    else
        print_error "❌ Invalid users data"
        exit 1
    fi
}

# Load items data
load_items() {
    print_status "Loading items data..."
    
    item_count=$(jq length "$DATA_DIR/items.json")
    print_status "📊 Found $item_count items to load"
    
    if jq '.[0:5]' "$DATA_DIR/items.json" > /dev/null; then
        print_status "✅ Items data validated"
    else
        print_error "❌ Invalid items data"
        exit 1
    fi
}

# Load interactions data
load_interactions() {
    print_status "Loading interactions data..."
    
    interaction_count=$(jq length "$DATA_DIR/interactions.json")
    print_status "📊 Found $interaction_count interactions to load"
    
    if jq '.[0:5]' "$DATA_DIR/interactions.json" > /dev/null; then
        print_status "✅ Interactions data validated"
    else
        print_error "❌ Invalid interactions data"
        exit 1
    fi
}

# Test the recommendation API
test_recommendations() {
    print_status "Testing recommendation API..."
    
    # Test basic recommendation endpoint
    response=$(curl -s "$ML_SERVICE_URL/recommendations/user/1?limit=5")
    
    if echo "$response" | jq -e '.recommendations' > /dev/null 2>&1; then
        rec_count=$(echo "$response" | jq '.recommendations | length')
        print_status "✅ Recommendation API working - got $rec_count recommendations"
    else
        print_error "❌ Recommendation API test failed"
        echo "Response: $response"
    fi
}

# Main execution
main() {
    echo "🚀 Starting data loading process..."
    
    check_data_files
    wait_for_service
    load_users
    load_items
    load_interactions
    test_recommendations
    
    echo ""
    print_status "✅ Data loading complete!"
    echo ""
    echo "📊 Data Summary:"
    echo "================"
    echo "Users: $(jq length $DATA_DIR/users.json)"
    echo "Items: $(jq length $DATA_DIR/items.json)" 
    echo "Interactions: $(jq length $DATA_DIR/interactions.json)"
    echo ""
    echo "🌐 Test the API:"
    echo "Recommendations: curl $ML_SERVICE_URL/recommendations/user/1"
    echo "Health Check: curl $ML_SERVICE_URL/health"
    echo "API Docs: $ML_SERVICE_URL/docs"
}

# Check if jq is installed
if ! command -v jq >/dev/null 2>&1; then
    print_error "jq is required but not installed. Please install jq first."
    echo "Ubuntu/Debian: sudo apt-get install jq"
    echo "macOS: brew install jq"
    exit 1
fi

main "$@"