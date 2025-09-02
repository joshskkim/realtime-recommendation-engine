// File: tests/performance/load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 200 }, // Ramp to 200
    { duration: '5m', target: 200 }, // Stay at 200
    { duration: '2m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    errors: ['rate<0.1'],              // Error rate under 10%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://api.yourdomain.com';

export default function () {
  const userId = `user_${Math.floor(Math.random() * 10000)}`;
  
  // Test 1: Get recommendations
  const recResponse = http.get(`${BASE_URL}/recommendations/user/${userId}?limit=10`);
  check(recResponse, {
    'recommendations status 200': (r) => r.status === 200,
    'recommendations response time < 500ms': (r) => r.timings.duration < 500,
  });
  errorRate.add(recResponse.status !== 200);
  
  sleep(1);
  
  // Test 2: Record interaction
  const interactionPayload = JSON.stringify({
    user_id: userId,
    item_id: `item_${Math.floor(Math.random() * 1000)}`,
    interaction_type: 'view',
    rating: Math.random() * 5,
  });
  
  const interactionResponse = http.post(
    `${BASE_URL}/interactions`,
    interactionPayload,
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  check(interactionResponse, {
    'interaction status 201': (r) => r.status === 201,
    'interaction response time < 200ms': (r) => r.timings.duration < 200,
  });
  errorRate.add(interactionResponse.status !== 201);
  
  sleep(2);
  
  // Test 3: Cache service
  const cacheKey = `test_${Math.random().toString(36).substring(7)}`;
  const cacheResponse = http.get(`${BASE_URL}/cache/${cacheKey}`);
  check(cacheResponse, {
    'cache response time < 50ms': (r) => r.timings.duration < 50,
  });
  
  sleep(1);
}