# File: terraform/elasticache.tf
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "recommendation-redis"
  replication_group_description = "Redis cluster for recommendation system"
  
  engine               = "redis"
  engine_version       = "7.0"
  node_type           = "cache.r6g.large"
  number_cache_clusters = 3
  
  automatic_failover_enabled = true
  multi_az_enabled          = true
  
  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  snapshot_retention_limit = 7
  snapshot_window         = "03:00-05:00"
  
  tags = {
    Name        = "recommendation-redis"
    Environment = "production"
  }
}