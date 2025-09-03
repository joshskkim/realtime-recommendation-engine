# ---------- Stage 1: Builder ----------
FROM python:3.13.7-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    g++ \
    gcc \
    gfortran \
    libffi-dev \
    libopenblas-dev \
    libpq-dev \
    pkg-config \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# ---------- Stage 2: Runtime ----------
FROM python:3.13.7-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev \
    libpq5 \
    openssl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app /app

# Create non-root user
RUN adduser --disabled-password --gecos '' --uid 1001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
