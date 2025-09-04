# API Specification

## Base URL
```
https://api.recommendation-engine.com/v1
```

## Authentication
All requests require Bearer token authentication:
```
Authorization: Bearer <token>
```

## Endpoints

### Get Recommendations
```http
GET /recommendations/{userId}
```

**Parameters:**
- `userId` (path): User identifier
- `limit` (query): Number of recommendations (default: 10)
- `category` (query): Filter by category (optional)

**Response:**
```json
{
  "status": "success",
  "userId": "user123",
  "recommendations": [
    {
      "productId": "prod456",
      "score": 0.95,
      "reason": "Based on your recent purchases",
      "category": "electronics"
    }
  ],
  "timestamp": "2025-09-03T20:30:00Z"
}
```

### Record User Event
```http
POST /events/interaction
```

**Request Body:**
```json
{
  "userId": "user123",
  "productId": "prod456",
  "eventType": "view|click|purchase|rating",
  "eventValue": 4.5,
  "timestamp": "2025-09-03T20:30:00Z"
}
```

### Get Trending Products
```http
GET /products/trending
```

**Parameters:**
- `timeframe` (query): Hour, day, week (default: day)
- `limit` (query): Number of products (default: 20)

### Retrain Model
```http
PUT /models/retrain
```

**Request Body:**
```json
{
  "modelType": "collaborative|content|hybrid",
  "dataset": "latest|custom",
  "parameters": {
    "epochs": 100,
    "batchSize": 32
  }
}
```

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "services": {
    "database": "connected",
    "redis": "connected",
    "kafka": "connected"
  }
}
```

## WebSocket Events

### Subscribe to Real-time Recommendations
```javascript
ws://api.recommendation-engine.com/ws/recommendations

// Subscribe
{ "action": "subscribe", "userId": "user123" }

// Receive updates
{
  "type": "recommendation",
  "data": {
    "productId": "prod789",
    "score": 0.92
  }
}
```

## Rate Limiting
- 1000 requests per minute per API key
- WebSocket: 100 messages per minute

## Error Codes
| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid token |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

## SDK Examples

### Python
```python
from recommendation_client import Client

client = Client(api_key="your_key")
recs = client.get_recommendations(user_id="user123")
```

### JavaScript
```javascript
const client = new RecommendationClient({ apiKey: 'your_key' });
const recs = await client.getRecommendations('user123');
```