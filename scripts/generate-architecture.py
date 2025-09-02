# File: scripts/generate_architecture.py
"""Generate architecture diagram using Python"""

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users
from diagrams.programming.framework import React, Angular
from diagrams.programming.language import NodeJS, Python, Csharp, Rust
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.queue import Kafka
from diagrams.onprem.monitoring import Prometheus, Grafana
from diagrams.onprem.container import Docker
from diagrams.k8s.compute import Pod
from diagrams.k8s.network import Service

with Diagram("Recommendation System Architecture", filename="docs/images/architecture", show=False):
    users = Users("Users")
    
    with Cluster("Client Applications"):
        web = React("Web App")
        mobile = Angular("Mobile App")
    
    with Cluster("API Gateway"):
        gateway = NodeJS("API Gateway\n(Node.js)")
    
    with Cluster("Microservices"):
        ml_service = Python("ML Service\n(FastAPI)")
        user_service = Csharp("User Service\n(.NET)")
        cache_service = Rust("Cache Service\n(Rust)")
    
    with Cluster("Stream Processing"):
        stream = Python("Stream Processor\n(Kafka Streams)")
    
    with Cluster("Data Layer"):
        postgres = PostgreSQL("PostgreSQL")
        redis = Redis("Redis Cache")
        kafka = Kafka("Kafka")
    
    with Cluster("Monitoring"):
        prometheus = Prometheus("Prometheus")
        grafana = Grafana("Grafana")
    
    # Connections
    users >> Edge(label="HTTPS") >> [web, mobile]
    [web, mobile] >> Edge(label="REST API") >> gateway
    
    gateway >> Edge(label="HTTP") >> ml_service
    gateway >> Edge(label="HTTP") >> user_service
    gateway >> Edge(label="HTTP") >> cache_service
    
    ml_service >> Edge(label="Query") >> redis
    ml_service >> Edge(label="Query") >> postgres
    user_service >> Edge(label="Query") >> postgres
    cache_service >> Edge(label="Get/Set") >> redis
    
    stream >> Edge(label="Consume") >> kafka
    ml_service >> Edge(label="Produce") >> kafka
    
    [ml_service, user_service, cache_service] >> Edge(label="Metrics") >> prometheus
    prometheus >> Edge(label="Query") >> grafana

print("Architecture diagram generated at docs/images/architecture.png")

# File: scripts/generate_performance_report.py
"""Generate performance metrics visualization"""

import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

# Generate sample data
time_points = [datetime.now() - timedelta(minutes=x) for x in range(60, 0, -1)]
latency_p50 = np.random.normal(32, 3, 60)
latency_p95 = np.random.normal(165, 10, 60)
latency_p99 = np.random.normal(420, 20, 60)
throughput = np.random.normal(12500, 500, 60)

fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('Real-time Performance Metrics', fontsize=16, fontweight='bold')

# Latency graph
ax1.plot(time_points, latency_p50, label='P50', color='green', linewidth=2)
ax1.plot(time_points, latency_p95, label='P95', color='orange', linewidth=2)
ax1.plot(time_points, latency_p99, label='P99', color='red', linewidth=2)
ax1.set_title('Response Latency (ms)')
ax1.set_xlabel('Time')
ax1.set_ylabel('Latency (ms)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Throughput graph
ax2.plot(time_points, throughput, color='blue', linewidth=2)
ax2.fill_between(time_points, throughput, alpha=0.3)
ax2.set_title('Throughput (Requests/sec)')
ax2.set_xlabel('Time')
ax2.set_ylabel('RPS')
ax2.grid(True, alpha=0.3)

# Cache hit rate
cache_hit_rate = np.random.normal(87, 2, 60)
ax3.plot(time_points, cache_hit_rate, color='purple', linewidth=2)
ax3.set_title('Cache Hit Rate (%)')
ax3.set_xlabel('Time')
ax3.set_ylabel('Hit Rate %')
ax3.set_ylim([80, 95])
ax3.grid(True, alpha=0.3)

# Error rate
error_rate = np.random.normal(0.05, 0.02, 60)
ax4.plot(time_points, error_rate, color='red', linewidth=2)
ax4.set_title('Error Rate (%)')
ax4.set_xlabel('Time')
ax4.set_ylabel('Error %')
ax4.set_ylim([0, 0.2])
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('docs/images/performance-metrics.png', dpi=150, bbox_inches='tight')
print("Performance metrics visualization saved to docs/images/performance-metrics.png")

# File: scripts/generate_ab_test_results.py
"""Generate A/B test results visualization"""

import matplotlib.pyplot as plt
import numpy as np

# Sample A/B test data
groups = ['Control', 'Variant A', 'Variant B']
conversion_rates = [5.2, 7.1, 6.8]
confidence_intervals = [(4.8, 5.6), (6.5, 7.7), (6.2, 7.4)]
sample_sizes = [5000, 5000, 5000]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('A/B Test Results - Recommendation Algorithm Comparison', fontsize=14, fontweight='bold')

# Conversion rates with confidence intervals
x_pos = np.arange(len(groups))
errors = [(ci[1] - ci[0])/2 for ci in confidence_intervals]
colors = ['#3498db', '#2ecc71', '#e74c3c']

bars = ax1.bar(x_pos, conversion_rates, yerr=errors, capsize=10, color=colors, alpha=0.8)
ax1.set_xlabel('Variant')
ax1.set_ylabel('Conversion Rate (%)')
ax1.set_title('Conversion Rates with 95% CI')
ax1.set_xticks(x_pos)
ax1.set_xticklabels(groups)

# Add value labels on bars
for bar, rate in zip(bars, conversion_rates):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             f'{rate}%', ha='center', va='bottom', fontweight='bold')

# Statistical significance
ax1.axhline(y=conversion_rates[0], color='gray', linestyle='--', alpha=0.5)
ax1.text(0.5, conversion_rates[0] + 0.1, 'Baseline', fontsize=10, alpha=0.7)

# Cumulative conversions over time
days = np.arange(1, 31)
control_cumulative = np.cumsum(np.random.binomial(170, 0.052, 30))
variant_a_cumulative = np.cumsum(np.random.binomial(170, 0.071, 30))
variant_b_cumulative = np.cumsum(np.random.binomial(170, 0.068, 30))

ax2.plot(days, control_cumulative, label='Control', color=colors[0], linewidth=2)
ax2.plot(days, variant_a_cumulative, label='Variant A', color=colors[1], linewidth=2)
ax2.plot(days, variant_b_cumulative, label='Variant B', color=colors[2], linewidth=2)
ax2.set_xlabel('Days')
ax2.set_ylabel('Cumulative Conversions')
ax2.set_title('Cumulative Conversions Over Time')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('docs/images/ab-testing-results.png', dpi=150, bbox_inches='tight')
print("A/B testing results saved to docs/images/ab-testing-results.png")

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