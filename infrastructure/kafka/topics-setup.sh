#!/bin/bash

# Kafka Topics Setup Script
# Creates all necessary topics for the recommendation engine

set -e

echo "🔧 Setting up Kafka topics for Real-time Recommendation Engine..."

# Kafka connection details
KAFKA_CONTAINER="kafka"
BOOTSTRAP_SERVERS="kafka:29092"

# Wait for Kafka to be ready
echo "⏳ Waiting for Kafka to be ready..."
timeout=60
while ! docker exec $KAFKA_CONTAINER kafka-broker-api-versions --bootstrap-server $BOOTSTRAP_SERVERS > /dev/null 2>&1; do
    echo "Waiting for Kafka..."
    sleep 5
    timeout=$((timeout - 5))
    if [ $timeout -le 0 ]; then
        echo "❌ Timeout waiting for Kafka to be ready"
        exit 1
    fi
done

echo "✅ Kafka is ready!"

# Function to create topic
create_topic() {
    local topic_name=$1
    local partitions=$2
    local replication_factor=$3
    local cleanup_policy=$4
    local retention_ms=$5
    
    echo "📝 Creating topic: $topic_name"
    
    if [ -n "$cleanup_policy" ] && [ -n "$retention_ms" ]; then
        docker exec $KAFKA_CONTAINER kafka-topics --create \
            --bootstrap-server $BOOTSTRAP_SERVERS \
            --topic $topic_name \
            --partitions $partitions \
            --replication-factor $replication_factor \
            --config cleanup.policy=$cleanup_policy \
            --config retention.ms=$retention_ms \
            --if-not-exists
    else
        docker exec $KAFKA_CONTAINER kafka-topics --create \
            --bootstrap-server $BOOTSTRAP_SERVERS \
            --topic $topic_name \
            --partitions $partitions \
            --replication-factor $replication_factor \
            --if-not-exists
    fi
        
    if [ $? -eq 0 ]; then
        echo "✅ Topic '$topic_name' created successfully"
    else
        echo "⚠️  Topic '$topic_name' might already exist"
    fi
}

# Create topics with appropriate configuration
echo "🚀 Creating Kafka topics..."

# User interaction events (high throughput)
create_topic "user-interactions" 6 1 "delete" "604800000" # 7 days

# User profile updates (moderate throughput)
create_topic "user-profiles" 3 1 "compact" "2592000000" # 30 days

# Content metadata updates (low throughput)
create_topic "content-metadata" 3 1 "compact" "7776000000" # 90 days

# Generated recommendations (moderate throughput)
create_topic "recommendations-generated" 6 1 "delete" "259200000" # 3 days

# Model update notifications (low throughput)
create_topic "model-updates" 1 1 "delete" "86400000" # 1 day

# A/B testing events
create_topic "ab-test-events" 3 1 "delete" "604800000" # 7 days

# System events and monitoring
create_topic "system-events" 3 1 "delete" "259200000" # 3 days

# Dead letter queue for failed messages
create_topic "dlq-failed-events" 3 1 "delete" "604800000" # 7 days

echo ""
echo "📋 Topic Summary:"
echo "=================="
docker exec $KAFKA_CONTAINER kafka-topics --list --bootstrap-server $BOOTSTRAP_SERVERS | grep -E "(user-interactions|user-profiles|content-metadata|recommendations-generated|model-updates|ab-test-events|system-events|dlq-failed-events)"

echo ""
echo "🔍 Topic Details:"
echo "=================="
for topic in user-interactions user-profiles content-metadata recommendations-generated model-updates ab-test-events system-events dlq-failed-events; do
    echo "📊 Topic: $topic"
    docker exec $KAFKA_CONTAINER kafka-topics --describe --bootstrap-server $BOOTSTRAP_SERVERS --topic $topic | head -2
    echo ""
done

echo "✅ All Kafka topics have been created successfully!"
echo ""
echo "🔧 Useful commands:"
echo "=================="
echo "# List all topics:"
echo "docker exec kafka kafka-topics --list --bootstrap-server kafka:29092"
echo ""
echo "# Describe a specific topic:"
echo "docker exec kafka kafka-topics --describe --bootstrap-server kafka:29092 --topic user-interactions"
echo ""
echo "# Consume messages from a topic:"
echo "docker exec kafka kafka-console-consumer --bootstrap-server kafka:29092 --topic user-interactions --from-beginning"
echo ""
echo "# Produce test messages:"
echo "docker exec -it kafka kafka-console-producer --bootstrap-server kafka:29092 --topic user-interactions"
echo ""
echo "🌐 Access Kafka UI at: http://localhost:8080"