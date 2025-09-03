FROM python:3.13.7-alpine3.22 AS builder

WORKDIR /app

# Install build dependencies for Alpine
RUN apk update && apk add --no-cache \
    g++ \
    gcc \
    musl-dev \
    openssl-dev \
    postgresql-dev \
    postgresql-libs \
    && rm -rf /var/cache/apk/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

FROM python:3.13.7-alpine3.22

WORKDIR /app

# Upgrade system packages
RUN apk update && apk upgrade -y --no-cache

# Install runtime dependencies only
RUN apk add --no-cache \
    postgresql-libs \
    openssl

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application
COPY . .

# Create non-root user
RUN adduser -D -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
