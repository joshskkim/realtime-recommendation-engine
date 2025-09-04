# Performance Tuning Guide

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API Response Time (p50) | < 50ms | 32ms |
| API Response Time (p99) | < 100ms | 45ms |
| Throughput | 10K req/s | 12.5K req/s |
| ML Model Inference | < 50ms | 28ms |
| Cache Hit Rate | > 90% | 94.2% |

## Database Optimization

### PostgreSQL Configuration
```sql
-- postgresql.conf
max_connections = 200
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
work_mem = 20MB
```

### Indexing Strategy
```sql
-- Critical indexes for performance
CREATE INDEX idx_user_interactions ON user_events(user_id, timestamp DESC);
CREATE INDEX idx_product_category ON products(category, score DESC);
CREATE INDEX idx_recommendations ON recommendations(user_id, created_at DESC);

-- Partial indexes for hot queries
CREATE INDEX idx_active_users ON users(id) WHERE active = true;
```

### Query Optimization
```sql
-- Use EXPLAIN ANALYZE for query planning
EXPLAIN ANALYZE
SELECT * FROM recommendations 
WHERE user_id = '123' 
AND created_at > NOW() - INTERVAL '1 hour';

-- Vacuum and analyze regularly
VACUUM ANALYZE recommendations;
```

## Redis Optimization

### Configuration
```redis
# redis.conf
maxmemory 8gb
maxmemory-policy allkeys-lru
tcp-keepalive 60
timeout 0
tcp-backlog 511

# Persistence settings
save 900 1
save 300 10
save 60 10000
```

### Caching Strategy
```javascript
// Implement cache warming
async function warmCache() {
  const hotProducts = await getTopProducts(100);
  for (const product of hotProducts) {
    await redis.setex(`product:${product.id}`, 3600, JSON.stringify(product));
  }
}

// Use pipeline for batch operations
const pipeline = redis.pipeline();
userIds.forEach(id => {
  pipeline.get(`user:${id}`);
});
const results = await pipeline.exec();
```

## Kafka Optimization

### Producer Settings
```javascript
{
  'compression.type': 'snappy',
  'batch.size': 32768,
  'linger.ms': 10,
  'buffer.memory': 33554432,
  'acks': 1
}
```

### Consumer Settings
```javascript
{
  'fetch.min