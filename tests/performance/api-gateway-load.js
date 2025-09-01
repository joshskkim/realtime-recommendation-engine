import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 200 },  // Ramp up to 200 users
    { duration: '5m', target: 200 },  // Stay at 200 users
    { duration: '2m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    errors: ['rate<0.1'],              // Error rate must be below 10%
  },
};

const BASE_URL = 'http://localhost:8080';

export default function () {
  // Test user recommendations endpoint
  const userId = `user${Math.floor(Math.random() * 1000)}`;
  const recommendationsRes = http.get(`${BASE_URL}/api/recommendations/user/${userId}?limit=10`);
  
  check(recommendationsRes, {
    'recommendations status is 200': (r) => r.status === 200,
    'recommendations response time < 500ms': (r) => r.timings.duration < 500,
    'recommendations response has items': (r) => {
      const body = JSON.parse(r.body);
      return body.items && body.items.length > 0;
    },
  });
  
  errorRate.add(recommendationsRes.status !== 200);
  
  sleep(1);
  
  // Test interaction recording
  const interactionRes = http.post(
    `${BASE_URL}/api/interactions`,
    JSON.stringify({
      user_id: userId,
      item_id: `item${Math.floor(Math.random() * 1000)}`,
      interaction_type: 'view',
      rating: Math.random() * 5,
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  check(interactionRes, {
    'interaction status is 201': (r) => r.status === 201,
    'interaction response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  errorRate.add(interactionRes.status !== 201);
  
  sleep(1);
  
  // Test trending items endpoint
  const trendingRes = http.get(`${BASE_URL}/api/recommendations/trending?limit=10`);
  
  check(trendingRes, {
    'trending status is 200': (r) => r.status === 200,
    'trending response time < 300ms': (r) => r.timings.duration < 300,
  });
  
  errorRate.add(trendingRes.status !== 200);
  
  sleep(1);
}