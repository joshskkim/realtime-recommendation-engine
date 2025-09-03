FROM node:lts-trixie-slim AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

RUN apk update && apk upgrade

# Install dependencies with security audit
RUN npm ci --only=production && \
    npm audit fix --force

# Copy application code
COPY . .

# Production stage
FROM node:lts-trixie-slim

WORKDIR /app

# Install dumb-init for proper signal handling
RUN apk update && apk upgrade && apk add --no-cache dumb-init

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Copy from builder
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --chown=nodejs:nodejs . .

USER nodejs

EXPOSE 3001

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "src/app.js"]