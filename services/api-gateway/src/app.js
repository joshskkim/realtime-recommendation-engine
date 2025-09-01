// services/api-gateway/src/app.js
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const axios = require('axios');
const { Kafka } = require('kafkajs');
const Redis = require('ioredis');
const winston = require('winston');
const prometheus = require('prom-client');

// Initialize logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});

// Initialize Prometheus metrics
const register = new prometheus.Registry();
prometheus.collectDefaultMetrics({ register });

const httpRequestDuration = new prometheus.Histogram({
  name: 'http_request_duration_ms',
  help: 'Duration of HTTP requests in ms',
  labelNames: ['method', 'route', 'status'],
  buckets: [1, 5, 10, 25, 50, 100, 250, 500, 1000]
});

const recommendationCacheHits = new prometheus.Counter({
  name: 'recommendation_cache_hits_total',
  help: 'Total number of recommendation cache hits'
});

const recommendationCacheMisses = new prometheus.Counter({
  name: 'recommendation_cache_misses_total',
  help: 'Total number of recommendation cache misses'
});

register.registerMetric(httpRequestDuration);
register.registerMetric(recommendationCacheHits);
register.registerMetric(recommendationCacheMisses);

// Initialize Express app
const app = express();

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(morgan('combined', { stream: { write: message => logger.info(message.trim()) } }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});

app.use('/api/', limiter);

// Redis client
const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: process.env.REDIS_PORT || 6379,
  retryStrategy: (times) => Math.min(times * 50, 2000)
});

redis.on('error', (err) => {
  logger.error('Redis Client Error', err);
});

redis.on('connect', () => {
  logger.info('Connected to Redis');
});

// Kafka producer
const kafka = new Kafka({
  clientId: 'api-gateway',
  brokers: (process.env.KAFKA_BROKERS || 'localhost:9092').split(','),
  retry: {
    initialRetryTime: 100,
    retries: 8
  }
});

const producer = kafka.producer();

// Service endpoints configuration
const services = {
  ml: {
    url: process.env.ML_SERVICE_URL || 'http://localhost:8000',
    timeout: 5000
  },
  user: {
    url: process.env.USER_SERVICE_URL || 'http://localhost:5001',
    timeout: 3000
  },
  cache: {
    url: process.env.CACHE_SERVICE_URL || 'http://localhost:8082',
    timeout: 1000
  }
};

// Helper function for service calls with circuit breaker pattern
class CircuitBreaker {
  constructor(name, threshold = 5, timeout = 60000) {
    this.name = name;
    this.failureCount = 0;
    this.threshold = threshold;
    this.timeout = timeout;
    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    this.nextAttempt = Date.now();
  }

  async call(fn) {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextAttempt) {
        throw new Error(`Circuit breaker is OPEN for ${this.name}`);
      }
      this.state = 'HALF_OPEN';
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  onSuccess() {
    this.failureCount = 0;
    this.state = 'CLOSED';
  }

  onFailure() {
    this.failureCount++;
    if (this.failureCount >= this.threshold) {
      this.state = 'OPEN';
      this.nextAttempt = Date.now() + this.timeout;
      logger.error(`Circuit breaker opened for ${this.name}`);
    }
  }
}

const circuitBreakers = {
  ml: new CircuitBreaker('ML Service'),
  user: new CircuitBreaker('User Service'),
  cache: new CircuitBreaker('Cache Service')
};

// Middleware for request timing
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    httpRequestDuration.labels(req.method, req.route?.path || req.url, res.statusCode).observe(duration);
  });
  next();
});

// Health check endpoint
app.get('/health', async (req, res) => {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    services: {
      redis: redis.status === 'ready',
      kafka: producer._producer ? true : false
    }
  };

  // Check downstream services
  try {
    await axios.get(`${services.ml.url}/health`, { timeout: 1000 });
    health.services.ml = true;
  } catch {
    health.services.ml = false;
    health.status = 'degraded';
  }

  try {
    await axios.get(`${services.user.url}/health`, { timeout: 1000 });
    health.services.user = true;
  } catch {
    health.services.user = false;
    health.status = 'degraded';
  }

  const statusCode = health.status === 'healthy' ? 200 : 503;
  res.status(statusCode).json(health);
});

// Metrics endpoint
app.get('/metrics', (req, res) => {
  res.set('Content-Type', register.contentType);
  register.metrics().then(data => res.end(data));
});

// Get recommendations for a user
app.get('/api/recommendations/user/:userId', async (req, res) => {
  const { userId } = req.params;
  const { limit = 10, strategy = 'hybrid' } = req.query;
  const cacheKey = `recommendations:${userId}:${strategy}:${limit}`;

  try {
    // Check cache first
    const cached = await redis.get(cacheKey);
    if (cached) {
      recommendationCacheHits.inc();
      logger.info(`Cache hit for user ${userId}`);
      return res.json(JSON.parse(cached));
    }

    recommendationCacheMisses.inc();

    // Fetch user profile from User Service
    const userProfile = await circuitBreakers.user.call(async () => {
      const response = await axios.get(`${services.user.url}/api/users/${userId}`, {
        timeout: services.user.timeout
      });
      return response.data;
    });

    // Get recommendations from ML Service
    const recommendations = await circuitBreakers.ml.call(async () => {
      const response = await axios.post(`${services.ml.url}/recommendations/generate`, {
        user_id: userId,
        user_profile: userProfile,
        limit: parseInt(limit),
        strategy: strategy
      }, {
        timeout: services.ml.timeout
      });
      return response.data;
    });

    // Cache the results
    await redis.setex(cacheKey, 300, JSON.stringify(recommendations)); // Cache for 5 minutes

    // Send event to Kafka
    await producer.send({
      topic: 'recommendations-generated',
      messages: [{
        key: userId.toString(),
        value: JSON.stringify({
          user_id: userId,
          timestamp: new Date().toISOString(),
          strategy,
          count: recommendations.items?.length || 0
        })
      }]
    });

    res.json(recommendations);
  } catch (error) {
    logger.error('Error getting recommendations:', error);
    res.status(500).json({ error: 'Failed to get recommendations', details: error.message });
  }
});

// Record user interaction
app.post('/api/interactions', async (req, res) => {
  const { user_id, item_id, interaction_type, rating, metadata } = req.body;

  try {
    // Validate input
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

    // Invalidate user's recommendation cache
    const cachePattern = `recommendations:${user_id}:*`;
    const keys = await redis.keys(cachePattern);
    if (keys.length > 0) {
      await redis.del(...keys);
      logger.info(`Invalidated ${keys.length} cache entries for user ${user_id}`);
    }

    // Update user profile via User Service
    await circuitBreakers.user.call(async () => {
      await axios.post(`${services.user.url}/api/users/${user_id}/interactions`, interaction, {
        timeout: services.user.timeout
      });
    });

    res.status(201).json({ message: 'Interaction recorded successfully', interaction });
  } catch (error) {
    logger.error('Error recording interaction:', error);
    res.status(500).json({ error: 'Failed to record interaction', details: error.message });
  }
});

// Get similar items
app.get('/api/recommendations/item/:itemId/similar', async (req, res) => {
  const { itemId } = req.params;
  const { limit = 5 } = req.query;
  const cacheKey = `similar_items:${itemId}:${limit}`;

  try {
    // Check cache
    const cached = await redis.get(cacheKey);
    if (cached) {
      return res.json(JSON.parse(cached));
    }

    // Get similar items from ML Service
    const similarItems = await circuitBreakers.ml.call(async () => {
      const response = await axios.get(`${services.ml.url}/recommendations/item/${itemId}/similar`, {
        params: { limit },
        timeout: services.ml.timeout
      });
      return response.data;
    });

    // Cache the results
    await redis.setex(cacheKey, 3600, JSON.stringify(similarItems)); // Cache for 1 hour

    res.json(similarItems);
  } catch (error) {
    logger.error('Error getting similar items:', error);
    res.status(500).json({ error: 'Failed to get similar items', details: error.message });
  }
});

// Get trending items
app.get('/api/recommendations/trending', async (req, res) => {
  const { category, limit = 10, timeWindow = '24h' } = req.query;
  const cacheKey = `trending:${category || 'all'}:${timeWindow}:${limit}`;

  try {
    // Check cache
    const cached = await redis.get(cacheKey);
    if (cached) {
      return res.json(JSON.parse(cached));
    }

    // Get trending items from ML Service
    const trending = await circuitBreakers.ml.call(async () => {
      const response = await axios.get(`${services.ml.url}/recommendations/trending`, {
        params: { category, limit, time_window: timeWindow },
        timeout: services.ml.timeout
      });
      return response.data;
    });

    // Cache for shorter time as trending changes frequently
    await redis.setex(cacheKey, 600, JSON.stringify(trending)); // Cache for 10 minutes

    res.json(trending);
  } catch (error) {
    logger.error('Error getting trending items:', error);
    res.status(500).json({ error: 'Failed to get trending items', details: error.message });
  }
});

// Batch recommendations endpoint
app.post('/api/recommendations/batch', async (req, res) => {
  const { user_ids, limit = 10, strategy = 'hybrid' } = req.body;

  if (!Array.isArray(user_ids) || user_ids.length === 0) {
    return res.status(400).json({ error: 'user_ids must be a non-empty array' });
  }

  if (user_ids.length > 100) {
    return res.status(400).json({ error: 'Maximum 100 users per batch request' });
  }

  try {
    const recommendations = await Promise.all(
      user_ids.map(async (userId) => {
        const cacheKey = `recommendations:${userId}:${strategy}:${limit}`;
        
        // Try cache first
        const cached = await redis.get(cacheKey);
        if (cached) {
          return { user_id: userId, recommendations: JSON.parse(cached) };
        }

        // Fetch from ML service
        try {
          const response = await axios.post(`${services.ml.url}/recommendations/generate`, {
            user_id: userId,
            limit,
            strategy
          }, {
            timeout: services.ml.timeout
          });
          
          // Cache the result
          await redis.setex(cacheKey, 300, JSON.stringify(response.data));
          
          return { user_id: userId, recommendations: response.data };
        } catch (error) {
          logger.error(`Failed to get recommendations for user ${userId}:`, error);
          return { user_id: userId, error: 'Failed to generate recommendations' };
        }
      })
    );

    res.json({ recommendations });
  } catch (error) {
    logger.error('Error in batch recommendations:', error);
    res.status(500).json({ error: 'Failed to process batch recommendations' });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  logger.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server
async function startServer() {
  try {
    // Connect to Kafka
    await producer.connect();
    logger.info('Connected to Kafka');

    const PORT = process.env.PORT || 3001;
    app.listen(PORT, () => {
      logger.info(`API Gateway running on port ${PORT}`);
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM signal received: closing HTTP server');
  await producer.disconnect();
  await redis.quit();
  process.exit(0);
});

module.exports = { app, startServer };

if (require.main === module) {
  startServer();
}