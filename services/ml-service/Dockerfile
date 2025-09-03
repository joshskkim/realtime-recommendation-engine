FROM python:3.13.7-alpine3.22 AS builder

WORKDIR /app

# Install build dependencies
RUN apk update && apk add --no-cache \
    g++ \
    gcc \
    libpq5 \
    libssl-dev \
    && rm -rf /var/cache/apk/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Production stage
FROM python:3.13.7-alpine3.22

WORKDIR /app

# Upgrade system packages
RUN apk update && apk upgrade -y --no-cache

# Copy installed Python packages
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
