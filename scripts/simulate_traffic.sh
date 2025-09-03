# File: scripts/simulate_traffic.sh
#!/bin/bash
# Simulate realistic traffic for demos

echo "🚀 Starting traffic simulation..."

# Function to generate random user interaction
generate_interaction() {
    local user_id="user_$(shuf -i 1-1000 -n 1)"
    local item_id="item_$(shuf -i 1-5000 -n 1)"
    local interaction_type=$(shuf -e view click purchase like -n 1)
    local rating=$(awk -v min=3 -v max=5 'BEGIN{srand(); print min+rand()*(max-min)}')
    
    curl -s -X POST http://localhost:8000/interactions \
        -H "Content-Type: application/json" \
        -d "{
            \"user_id\": \"$user_id\",
            \"item_id\": \"$item_id\",
            \"interaction_type\": \"$interaction_type\",
            \"rating\": $rating
        }" > /dev/null
    
    echo "✅ User: $user_id → Item: $item_id ($interaction_type)"
}

# Generate continuous traffic
while true; do
    for i in {1..10}; do
        generate_interaction &
    done
    wait
    sleep 1
done