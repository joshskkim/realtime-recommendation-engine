// src/services/cacheService.js
const axios = require('axios');
const logger = require('../utils/logger');

class CacheService {
  constructor() {
    this.baseUrl = process.env.CACHE_SERVICE_URL || 'http://localhost:8001';
    this.timeout = 5000; // 5 second timeout
    this.fallbackToRedis = true;
  }

  async getRecommendations(userId, algorithm = 'default') {
    try {
      const response = await axios.get(
        `${this.baseUrl}/api/recommendations/${userId}`,
        {
          params: { algorithm },
          timeout: this.timeout
        }
      );
      
      logger.debug(`Cache hit for user ${userId}`, {
        algorithm,
        itemCount: response.data?.length || 0,
        source: 'rust-cache'
      });
      
      return response.data;
    } catch (error) {
      if (error.response?.status === 404) {
        logger.debug(`Cache miss for user ${userId}`, { algorithm });
        return null;
      }
      
      logger.error('Cache service error:', {
        error: error.message,
        userId,
        algorithm,
        status: error.response?.status
      });
      
      return null;
    }
  }

  async setRecommendations(userId, recommendations, ttlSeconds = 3600, algorithm = 'default') {
    try {
      await axios.post(
        `${this.baseUrl}/api/recommendations/${userId}`,
        {
          key: `rec:user:${userId}:${algorithm}`,
          value: recommendations,
          ttl_seconds: ttlSeconds
        },
        { timeout: this.timeout }
      );
      
      logger.debug(`Cached recommendations for user ${userId}`, {
        algorithm,
        itemCount: recommendations?.length || 0,
        ttl: ttlSeconds
      });
      
      return true;
    } catch (error) {
      logger.error('Cache set error:', {
        error: error.message,
        userId,
        algorithm
      });
      
      return false;
    }
  }

  async invalidateUser(userId) {
    try {
      await axios.delete(
        `${this.baseUrl}/api/cache/invalidate/rec:user:${userId}`,
        { timeout: this.timeout }
      );
      
      logger.info(`Invalidated cache for user ${userId}`);
      return true;
    } catch (error) {
      logger.error('Cache invalidation error:', {
        error: error.message,
        userId
      });
      
      return false;
    }
  }

  async getStats() {
    try {
      const response = await axios.get(
        `${this.baseUrl}/api/cache/stats`,
        { timeout: this.timeout }
      );
      
      return response.data;
    } catch (error) {
      logger.error('Cache stats error:', error.message);
      return null;
    }
  }

  async healthCheck() {
    try {
      await axios.get(`${this.baseUrl}/health`, { timeout: 2000 });
      return true;
    } catch (error) {
      return false;
    }
  }
}

module.exports = new CacheService();