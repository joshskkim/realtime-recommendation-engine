// src/app.js - Updated with Rust Cache Service Integration
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const axios = require('axios');
const redis = require('redis');
const { Kafka } = require('kafkajs');

const logger = require('./utils/logger');
const circuitBreakers = require('./utils/circuitBreaker');
const cacheService = require('./services/cacheService'); // New cache service

const app = express();
const port = process.env.PORT || 3001;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000, // limit each IP to 1000 requests per windowMs
  standardHeaders: true,
  legacyHeaders: false,
});
app.use(limiter);

// Service URLs
const services = {
  ml: {
    url: process.env.ML_SERVICE_URL || 'http://localhost:8000',
    timeout: 30000
  },
  user: {
    url: process.env.USER_SERVICE_URL || 'http://localhost:5001',
    timeout: 10000
  }
};

// Redis fallback client (for when cache service is unavailable)
let redisClient;
try {
  redisClient = redis.createClient({
    url: process.env.REDIS_URL || 'redis://localhost:6379'
  });
  redisClient.connect();
} catch (error) {
  logger.error('Redis connection failed:', error);
}

// Kafka producer
const kafka = new Kafka({
  clientId: 'api-gateway',
  brokers: [process.env.KAFKA_BROKER || 'localhost:29092']
});
const producer = kafka.producer();

// Health check endpoint
app.get('/health', async (req, res) => {
  const health = {
    service: 'api-gateway',
    status: 'healthy',
    timestamp: new Date().toISOString(),
    dependencies: {}
  };

  // Check cache service
  health.dependencies.cache = await cacheService.healthCheck();
  
  // Check other services
  try {
    await axios.get(`${services.ml.url}/health`, { timeout: 5000 });
    health.dependencies.ml_service = true;
  } catch (error) {
    health.dependencies.ml_service = false;
  }

  try {
    await axios.get(`${services.user.url}/health`, { timeout: 5000 });
    health.dependencies.user_service = true;
  } catch (error) {
    health.dependencies.user_service = false;
  }

  const allHealthy = Object.values(health.dependencies).every(Boolean);
  res.status(allHealthy ? 200 : 503).json(health);
});

// Enhanced recommendations endpoint with multi-tier caching
app.get('/api/recommendations/user/:userId', async (req, res) => {
  const { userId } = req.params;
  const { limit = 10, algorithm = 'collaborative', category, refresh } = req.query;
  
  const startTime = Date.now();
  
  try {
    // Skip cache if refresh is requested
    let recommendations = null;
    
    if (!refresh) {
      // Try Rust cache service first
      recommendations = await cacheService.getRecommendations(userId, algorithm);
      
      // Fallback to Redis if cache service unavailable
      if (!recommendations && redisClient) {
        const cacheKey = `rec:user:${userId}:${algorithm}`;
        const cached = await redisClient.get(cacheKey);
        if (cached) {
          recommendations = JSON.parse(cached);
          logger.debug('Cache hit from Redis fallback', { userId, algorithm });
        }
      }
    }

    // If not in cache, fetch from ML service
    if (!recommendations) {
      logger.info('Cache miss - fetching from ML service', { userId, algorithm });
      
      const mlResponse = await circuitBreakers.ml.call(async () => {
        return axios.post(`${services.ml.url}/api/recommendations/user`, {
          user_id: userId,
          algorithm,
          limit: parseInt(limit),
          category
        }, { timeout: services.ml.timeout });
      });

      recommendations = mlResponse.data.items || [];
      
      // Cache the results in both cache service and Redis
      await cacheService.setRecommendations(userId, recommendations, 3600, algorithm);
      
      if (redisClient) {
        const cacheKey = `rec:user:${userId}:${algorithm}`;
        await redisClient.setex(cacheKey, 3600, JSON.stringify(recommendations));
      }
    }

    const responseTime = Date.now() - startTime;
    
    res.json({
      user_id: userId,
      algorithm,
      items: recommendations.slice(0, parseInt(limit)),
      metadata: {
        response_time_ms: responseTime,
        cached: !refresh,
        item_count: recommendations.length,
        generated_at: new Date().toISOString()
      }
    });

  } catch (error) {
    logger.error('Error getting recommendations:', {
      error: error.message,
      userId,
      algorithm,
      responseTime: Date.now() - startTime
    });

    res.status(500).json({
      error: 'Failed to get recommendations',
      details: error.message
    });
  }
});

// Enhanced interaction recording with cache invalidation
app.post('/api/interactions', async (req, res) => {
  const { user_id, item_id, interaction_type, rating, metadata } = req.body;

  try {
    if (!user_id || !item_id || !interaction_type) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const interaction = {
      user_id,
      item_id,
      interaction_type,
      rating,
      metadata,
      timestamp: new Date().toISOString()
    };

    // Send to Kafka for real-time processing
    await producer.send({
      topic: 'user-interactions',
      messages: [{
        key: user_id.toString(),
        value: JSON.stringify(interaction)
      }]
    });

    // Invalidate user's cache in cache service
    await cacheService.invalidateUser(user_id);
    
    // Fallback Redis cache invalidation
    if (redisClient) {
      const cachePattern = `rec:user:${user_id}:*`;
      const keys = await redisClient.keys(cachePattern);
      if (keys.length > 0) {
        await redisClient.del(...keys);
      }
    }

    // Update user profile
    await circuitBreakers.user.call(async () => {
      await axios.post(
        `${services.user.url}/api/users/${user_id}/interactions`,
        interaction,
        { timeout: services.user.timeout }
      );
    });

    logger.info('Interaction recorded and cache invalidated', {
      user_id,
      item_id,
      interaction_type
    });

    res.status(201).json({
      message: 'Interaction recorded successfully',
      interaction
    });

  } catch (error) {
    logger.error('Error recording interaction:', {
      error: error.message,
      user_id,
      item_id,
      interaction_type
    });

    res.status(500).json({
      error: 'Failed to record interaction',
      details: error.message
    });
  }
});

// Cache management endpoints
app.get('/api/cache/stats', async (req, res) => {
  try {
    const stats = await cacheService.getStats();
    res.json(stats || { error: 'Cache service unavailable' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.delete('/api/cache/invalidate/:pattern', async (req, res) => {
  const { pattern } = req.params;
  
  try {
    // Invalidate in cache service
    const success = await cacheService.invalidateUser(pattern);
    
    // Also invalidate Redis fallback
    if (redisClient) {
      const keys = await redisClient.keys(`*${pattern}*`);
      if (keys.length > 0) {
        await redisClient.del(...keys);
      }
    }
    
    res.json({
      success,
      pattern,
      message: 'Cache invalidated'
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Batch recommendations with parallel cache lookups
app.post('/api/recommendations/batch', async (req, res) => {
  const { user_ids, limit = 10, algorithm = 'collaborative' } = req.body;
  
  if (!user_ids || !Array.isArray(user_ids)) {
    return res.status(400).json({ error: 'user_ids must be an array' });
  }
  
  if (user_ids.length > 100) {
    return res.status(400).json({ error: 'Maximum 100 users per batch request' });
  }
  
  const startTime = Date.now();
  
  try {
    // Parallel cache lookups
    const cachePromises = user_ids.map(userId => 
      cacheService.getRecommendations(userId, algorithm)
    );
    
    const cacheResults = await Promise.allSettled(cachePromises);
    const recommendations = {};
    const missingUsers = [];
    
    cacheResults.forEach((result, index) => {
      const userId = user_ids[index];
      if (result.status === 'fulfilled' && result.value) {
        recommendations[userId] = result.value.slice(0, limit);
      } else {
        missingUsers.push(userId);
      }
    });
    
    // Fetch missing recommendations from ML service
    if (missingUsers.length > 0) {
      const mlResponse = await circuitBreakers.ml.call(async () => {
        return axios.post(`${services.ml.url}/api/recommendations/batch`, {
          user_ids: missingUsers,
          algorithm,
          limit
        }, { timeout: services.ml.timeout });
      });
      
      // Cache the new recommendations
      const cachePromises = missingUsers.map(async (userId, index) => {
        const userRecs = mlResponse.data.recommendations[userId] || [];
        await cacheService.setRecommendations(userId, userRecs, 3600, algorithm);
        recommendations[userId] = userRecs;
      });
      
      await Promise.allSettled(cachePromises);
    }
    
    res.json({
      recommendations,
      algorithm,
      metadata: {
        response_time_ms: Date.now() - startTime,
        total_users: user_ids.length,
        cache_hits: user_ids.length - missingUsers.length,
        cache_misses: missingUsers.length
      }
    });
    
  } catch (error) {
    logger.error('Batch recommendations error:', error);
    res.status(500).json({ error: 'Failed to get batch recommendations' });
  }
});

// Initialize and start server
async function startServer() {
  try {
    await producer.connect();
    logger.info('Connected to Kafka');
    
    app.listen(port, () => {
      logger.info(`API Gateway listening on port ${port}`);
      logger.info('Cache service integration enabled');
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();