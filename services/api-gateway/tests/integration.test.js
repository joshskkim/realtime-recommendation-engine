const request = require('supertest');
const { app } = require('../src/app');
const Redis = require('ioredis');
const axios = require('axios');

// Mock external dependencies
jest.mock('ioredis');
jest.mock('axios');
jest.mock('kafkajs', () => ({
  Kafka: jest.fn(() => ({
    producer: () => ({
      connect: jest.fn(),
      send: jest.fn(),
      disconnect: jest.fn()
    })
  }))
}));

describe('API Gateway Integration Tests', () => {
  let redisClient;

  beforeEach(() => {
    // Setup Redis mock
    redisClient = {
      get: jest.fn(),
      setex: jest.fn(),
      del: jest.fn(),
      keys: jest.fn(),
      quit: jest.fn(),
      on: jest.fn(),
      status: 'ready'
    };
    Redis.mockImplementation(() => redisClient);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('GET /health', () => {
    it('should return healthy status when all services are up', async () => {
      axios.get.mockResolvedValue({ data: { status: 'healthy' } });

      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toHaveProperty('status', 'healthy');
      expect(response.body.services).toHaveProperty('redis', true);
    });

    it('should return degraded status when a service is down', async () => {
      axios.get.mockRejectedValue(new Error('Service unavailable'));

      const response = await request(app)
        .get('/health')
        .expect(503);

      expect(response.body).toHaveProperty('status', 'degraded');
    });
  });

  describe('GET /api/recommendations/user/:userId', () => {
    it('should return cached recommendations if available', async () => {
      const cachedData = JSON.stringify({
        items: [
          { item_id: '1', score: 0.95 },
          { item_id: '2', score: 0.89 }
        ]
      });
      redisClient.get.mockResolvedValue(cachedData);

      const response = await request(app)
        .get('/api/recommendations/user/user123')
        .expect(200);

      expect(response.body.items).toHaveLength(2);
      expect(redisClient.get).toHaveBeenCalledWith('recommendations:user123:hybrid:10');
    });

    it('should fetch from services when cache miss', async () => {
      redisClient.get.mockResolvedValue(null);
      
      axios.get.mockResolvedValue({
        data: {
          userId: 'user123',
          username: 'testuser',
          profile: { age: 25 }
        }
      });

      axios.post.mockResolvedValue({
        data: {
          items: [
            { item_id: '1', score: 0.95 },
            { item_id: '2', score: 0.89 }
          ]
        }
      });

      const response = await request(app)
        .get('/api/recommendations/user/user123?limit=5')
        .expect(200);

      expect(response.body.items).toHaveLength(2);
      expect(redisClient.setex).toHaveBeenCalled();
    });

    it('should handle service errors gracefully', async () => {
      redisClient.get.mockResolvedValue(null);
      axios.get.mockRejectedValue(new Error('User service error'));

      const response = await request(app)
        .get('/api/recommendations/user/user123')
        .expect(500);

      expect(response.body).toHaveProperty('error');
    });
  });

  describe('POST /api/interactions', () => {
    it('should record interaction successfully', async () => {
      axios.post.mockResolvedValue({ data: { success: true } });
      redisClient.keys.mockResolvedValue(['recommendations:user123:hybrid:10']);

      const response = await request(app)
        .post('/api/interactions')
        .send({
          user_id: 'user123',
          item_id: 'item456',
          interaction_type: 'view',
          rating: 4.5
        })
        .expect(201);

      expect(response.body).toHaveProperty('message', 'Interaction recorded successfully');
      expect(redisClient.del).toHaveBeenCalled();
    });

    it('should validate required fields', async () => {
      const response = await request(app)
        .post('/api/interactions')
        .send({
          user_id: 'user123'
          // Missing required fields
        })
        .expect(400);

      expect(response.body).toHaveProperty('error', 'Missing required fields');
    });
  });

  describe('GET /api/recommendations/trending', () => {
    it('should return trending items', async () => {
      const trendingData = JSON.stringify({
        items: [
          { item_id: 'trending1', score: 100 },
          { item_id: 'trending2', score: 95 }
        ]
      });
      redisClient.get.mockResolvedValue(trendingData);

      const response = await request(app)
        .get('/api/recommendations/trending?category=electronics')
        .expect(200);

      expect(response.body.items).toHaveLength(2);
    });
  });

  describe('POST /api/recommendations/batch', () => {
    it('should process batch recommendations', async () => {
      redisClient.get.mockResolvedValue(null);
      axios.post.mockResolvedValue({
        data: {
          items: [{ item_id: '1', score: 0.9 }]
        }
      });

      const response = await request(app)
        .post('/api/recommendations/batch')
        .send({
          user_ids: ['user1', 'user2'],
          limit: 5
        })
        .expect(200);

      expect(response.body.recommendations).toHaveLength(2);
    });

    it('should reject large batch requests', async () => {
      const userIds = Array(101).fill('user');

      const response = await request(app)
        .post('/api/recommendations/batch')
        .send({
          user_ids: userIds
        })
        .expect(400);

      expect(response.body).toHaveProperty('error', 'Maximum 100 users per batch request');
    });
  });
});
