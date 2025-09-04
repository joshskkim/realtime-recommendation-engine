# Security Overview

## Security Architecture

### Defense in Depth
We implement multiple layers of security controls:
1. **Network Security**: Firewalls, VPCs, Security Groups
2. **Application Security**: Input validation, authentication, authorization
3. **Data Security**: Encryption at rest and in transit
4. **Operational Security**: Monitoring, logging, incident response

## Authentication & Authorization

### OAuth 2.0 Implementation
```javascript
// JWT Token Structure
{
  "sub": "user123",
  "email": "user@example.com",
  "roles": ["user", "premium"],
  "exp": 1693785600,
  "iat": 1693699200
}
```

### API Key Management
```javascript
// Secure API key validation
const crypto = require('crypto');

function validateApiKey(apiKey) {
  const hash = crypto.createHash('sha256').update(apiKey).digest('hex');
  return database.checkApiKeyHash(hash);
}
```

### Role-Based Access Control (RBAC)
```javascript
const permissions = {
  'admin': ['read', 'write', 'delete', 'manage'],
  'developer': ['read', 'write'],
  'user': ['read'],
  'guest': ['read:public']
};

middleware.authorize = (requiredPermission) => {
  return (req, res, next) => {
    const userRole = req.user.role;
    if (permissions[userRole].includes(requiredPermission)) {
      next();
    } else {
      res.status(403).json({ error: 'Forbidden' });
    }
  };
};
```

## Data Protection

### Encryption at Rest
```yaml
# PostgreSQL encryption
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = 'server.crt';
ALTER SYSTEM SET ssl_key_file = 'server.key';

# Redis encryption
requirepass "strong_password_here"
tls-port 6379
tls-cert-file /path/to/redis.crt
tls-key-file /path/to/redis.key
```

### Encryption in Transit
```nginx
# TLS 1.3 Configuration
ssl_protocols TLSv1.3;
ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_stapling on;
ssl_stapling_verify on;
```

### PII Data Handling
```python
# Encrypt sensitive fields
from cryptography.fernet import Fernet

class PIIEncryption:
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def encrypt_pii(self, data):
        encrypted = {}
        for field in ['email', 'phone', 'ssn']:
            if field in data:
                encrypted[field] = self.cipher.encrypt(data[field].encode())
        return encrypted
    
    def decrypt_pii(self, data):
        decrypted = {}
        for field in ['email', 'phone', 'ssn']:
            if field in data:
                decrypted[field] = self.cipher.decrypt(data[field]).decode()
        return decrypted
```

## Input Validation & Sanitization

### Request Validation
```javascript
const Joi = require('joi');

const schemas = {
  userRegistration: Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().min(8).pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/).required(),
    age: Joi.number().min(13).max(120)
  }),
  
  productSearch: Joi.object({
    query: Joi.string().max(100).regex(/^[a-zA-Z0-9\s]+$/),
    limit: Joi.number().min(1).max(100)
  })
};

middleware.validate = (schema) => {
  return (req, res, next) => {
    const { error } = schema.validate(req.body);
    if (error) {
      res.status(400).json({ error: error.details[0].message });
    } else {
      next();
    }
  };
};
```

### SQL Injection Prevention
```javascript
// Use parameterized queries
const query = 'SELECT * FROM users WHERE id = $1 AND active = $2';
const values = [userId, true];
const result = await pool.query(query, values);

// Never do this
// const query = `SELECT * FROM users WHERE id = ${userId}`;
```

## Security Headers

```javascript
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));

app.use((req, res, next) => {
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
  next();
});
```

## Secrets Management

### Environment Variables
```bash
# .env.production (never commit this)
DB_PASSWORD=use_aws_secrets_manager
JWT_SECRET=use_aws_secrets_manager
API_KEY=use_aws_secrets_manager
```

### AWS Secrets Manager
```javascript
const AWS = require('aws-sdk');
const secretsManager = new AWS.SecretsManager();

async function getSecret(secretName) {
  try {
    const data = await secretsManager.getSecretValue({ SecretId: secretName }).promise();
    return JSON.parse(data.SecretString);
  } catch (error) {
    console.error('Error retrieving secret:', error);
    throw error;
  }
}
```

## Monitoring & Auditing

### Security Event Logging
```javascript
const winston = require('winston');

const securityLogger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'security.log' })
  ]
});

function logSecurityEvent(event, userId, details) {
  securityLogger.info({
    timestamp: new Date().toISOString(),
    event,
    userId,
    details,
    ip: req.ip,
    userAgent: req.headers['user-agent']
  });
}
```

### Intrusion Detection
```javascript
// Rate limiting per IP
const rateLimiter = new Map();

function detectBruteForce(ip) {
  const attempts = rateLimiter.get(ip) || 0;
  if (attempts > 5) {
    logSecurityEvent('BRUTE_FORCE_DETECTED', null, { ip, attempts });
    return true;
  }
  rateLimiter.set(ip, attempts + 1);
  setTimeout(() => rateLimiter.delete(ip), 900000); // 15 minutes
  return false;
}
```

## Vulnerability Management

### Dependency Scanning
```json
{
  "scripts": {
    "security:check": "npm audit && snyk test",
    "security:fix": "npm audit fix && snyk wizard"
  }
}
```

### Container Scanning
```dockerfile
# Dockerfile security best practices
FROM node:18-alpine AS builder
USER node
WORKDIR /app
COPY --chown=node:node package*.json ./
RUN npm ci --only=production

FROM gcr.io/distroless/nodejs18-debian11
COPY --from=builder /app /app
WORKDIR /app
EXPOSE 3000
CMD ["app.js"]
```

## Compliance

### GDPR Compliance
- Right to be forgotten: Implement data deletion APIs
- Data portability: Export user data in machine-readable format
- Consent management: Track and respect user preferences
- Privacy by design: Minimize data collection

### OWASP Top 10 Mitigation
1. **Injection**: Parameterized queries, input validation
2. **Broken Authentication**: Strong password policies, MFA
3. **Sensitive Data Exposure**: Encryption, secure transmission
4. **XML External Entities**: Disable XML external entity processing
5. **Broken Access Control**: RBAC, principle of least privilege
6. **Security Misconfiguration**: Hardened configurations, security headers
7. **Cross-Site Scripting**: Content Security Policy, output encoding
8. **Insecure Deserialization**: Input validation, type checking
9. **Using Components with Known Vulnerabilities**: Regular updates, scanning
10. **Insufficient Logging**: Comprehensive audit logs, monitoring

## Incident Response

### Response Plan
1. **Detection**: Automated alerts, monitoring
2. **Containment**: Isolate affected systems
3. **Investigation**: Log analysis, forensics
4. **Remediation**: Patch vulnerabilities, update configurations
5. **Recovery**: Restore services, verify integrity
6. **Lessons Learned**: Post-mortem, update procedures
