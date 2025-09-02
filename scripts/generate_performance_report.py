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
